from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session, flash, stream_with_context
import json
from sqlalchemy import create_engine
import pandas as pd
import pickle
import os
import faiss
from sentence_transformers import SentenceTransformer
from my_tools import retrieve_stock_data,convert_to_months,clarification_needed,calculate_max_loan_amount_from_monthly_payment,calculate_monthly_payment_with_interest,education_ranking
import numpy as np
from my_tools import tools


import openai




# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')
all_chunks_path = os.path.join('/Users/sondosali/Desktop/vectara_agentic',"finance_chunks.pkl")
embeddings_path = os.path.join('/Users/sondosali/Desktop/vectara_agentic',"finance_multi_table.index")






# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')
openai.api_key =  # Replace with your real key

schema_markdown = ''' # Financial Database Schema

 

## Tables


### `customer_balances` *contains customer current balances in their bank account* columns:

- `customerid` (PK, UUID) → unique ID for each customer

- `currentbalance` (numeric(12,2)) → Current amount of money the customer own in saudi riyals.



 

### `customer_commitments`  *contains the names of the commitments and thier total prices* columns:

- `customerid` (UUID, FK → demographics.customerid) → foreign customer IDs refering to the primary key in demographics table.

- `commitmentid` (PK, UUID) → unique IDs for the commitments based on the name and the customer.

- `commitmentname` (text) → The name of the commitment. Distinct values: ['school fees','house fees','tamara'].

- `commitmentprice` (numeric) → The total price of the commitment that the customer must pay over the duration time period. 

- `commitmentduration` (integer) → this is the commitment duration in MONTHS you can divide the commitment price by the commitmentduration to find the commitment price their month . A customer can have more than one commitment. 

 

### `customer_transaction` *contains customer financial transactions like deposits and money witdrawals* columns:

- `transactionid` (PK, UUID) → unique ID for every transaction any customer request.

- `customerid` (UUID, FK → demographics.customerid) → foreign customer ID refering to the primary unique key in demographics table.

- `date` (date) → The date the transaction happened. Formatted in: 'yyyy-mm-dd'

- `transactiontype` (varchar(50)) → The type of the transaction happened. Distinct values: ['Withdrawal', 'Deposit', 'Transfer']

- `channel` (varchar(50)) → The setting of the transaction. Where did the transaction happened. Distinct values: ['Branch', 'ATM', 'Online']

- `amount` (numeric) → The amount of money of the transaction in saudi riyals. 

 

### `demographics` *contains customer information*

- `customerid` (PK, UUID) → a unique ID for each customer.

- `firstname` (text) → The first name of a customer. (not unique)

- `lastname` (text) → The last or family name of a customer. (not unique)

- `gender` (text) → The gender of each customer. can be ['Male', 'Female']

- `age` (integer) → Customer's age in years. can vary from 18-80 years.

- `maritalstatus` (text) → The marital status of the customer. Distinct values include ['single', 'married', 'divorced', 'widowed'].

- `education` (text) → The highest education level of the customer. 

- `employmentstatus` (text) → The employment status of the customer.  Distinct values include ['employed', 'unemployed','retired','self-employed','student']

- `country` (text) → The customer's origin country.

- `city` (text) → The city where the customer is currently residing.

- `salary` (integer) → The customer's salary per month

 
### `orders` * this shows the orders customers have already made *

- `customerid` (UUID, FK → demographics.customerid) → the customer id

- `orderid` (PK, UUID)  the unique order id representing a certain order made by the customer

- `orderdate` (date) → the data in which the customer has made the order

- `quantity`  (integer) → the number of items of this product that the customer has ordered

- `totalamount` (numeric(10,2)) → amount that the customer has paid

- `orderstatus` (varchar(50)) → status of the customers order

- `productid`  (UUID, FK → products.productid) → the id of the product the customer has ordered on a specific date


 

### `products  these are the products available for you`

- `productid`  (PK, UUID) the unique product id for every product

- `productname`  (varchar(100))  the name of the product

- `category` (varchar(100))  the product category like 

- `price` (numeric(10,2)) the price of the product

- `quantity` (integer)  number of items of the  product  such as Electronics

- `availability` (varchar(50)) weather the product is on stock or out of stock 

- `manufacturer` (varchar(100)) product manufacturer such as Apple samsung , etc .. 

- `model` (varchar(100))  the model of the phone or the laptop such as Iphone 15  or similar

- `producttype` (varchar(50))  type of the product such as [Phone, laptop TV , speaker , Headphones , Camera , etc ...]

 

## Relationships

1. `customer_balances.customerid` → `demographics.customerid`

2. `customer_commitments.customerid` → `demographics.customerid`

3. `customer_transaction.customerid` → `demographics.customerid`

4. `orders.customerid` → `demographics.customerid`

5. `orders.productid` → `products.productid`


## Instructions

- Strictly do not consider customer commitments unless explicilty said to do so.

- When asked about customers salary given a period of time , remember to multiply the salary by the time period in months

- customer salaries are salaries per month 

'''


def RAG(query) :
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    D, I = index.search(query_embedding, k=5)
    retrieved_texts = [docs[i]['text'] for i in I[0]]
    return retrieved_texts

def add_message_to_chat(messages_array, message , entity , function_name = None, tool_call_id=None):
    message_dict = {}
    
    if entity == 'tool' :
        message_dict["role"] = entity  
        message_dict["name"] = function_name
        message_dict["content"] = message
        message_dict["tool_call_id"] = tool_call_id
    else:
        message_dict["role"] = entity  
        message_dict["content"] = message
    
    messages_array.append(message_dict)
   
   



def clean_queue(messages_arr):
    
    init_sys_prompt = {"role": "system", "content": (

      "You are an expert SQL assistant. You have access to this schema and your job is to give the customer the SQL statement to run. "
      "These stataments will later on be run as a python string so please take into account to escape speecial characters . e.g. % could be escaped by %% , etc..  The queries should be ending with a semicolon (;)"
      "Only use the `clarification_needed` tool **if the customer's name or product name is incomplete or ambiguous**. "
      "Do not use it if both first and last names are provided."
    )}
    print("cleaning")
    if len(messages_arr) == 0:
        messages_arr.append(init_sys_prompt)
        
    else:
        messages_arr=[messages_arr[0]]
        ##print("in the clean queue function ****** ---- messages array -----  ",messages_arr )
        
    print("cleaning done")
    return messages_arr
        #print("message array cleaned -- only system prompt resides")



def generate_response(query, messages_arr , initialization):
    
    retrieved = RAG(query)
     
    if initialization:   ### if it was the first QUERY then needs to be added to the prompt
        messages_arr = clean_queue(messages_arr)
        
        prompt = (
        f"You are a helpful financial assistant. Based on the following customer data, and the following schema {schema_markdown}  "
        "Use the tool `calculate_monthly_payment_with_interest` whenever the question involves loan amount, duration, monthly payment, or eligibility.\n"
        "Use the tool `education_ranking` whenever the question involves education OR DEGREES of eductation \n"
        "Use the tool clariciation_needed whenever the provided details aren't enough to identify the exact individual such as first name without a last name or the word iphone without the model. but iphone ## should be fine"
        "answer the user's question using the provided information. you should call the tools like the tool get education_data whenever the question is related to education or similar\n\n "
        "Context:\n"
        + "\n\n" +
        f"\n\nQuestion: {query}\n and here is some retrieved text that might help you to understand how the data looks like {retrieved} \n do not use numbers from this information but instead , learn how my data looks like and use the column names instead Answer:"
    )
        add_message_to_chat(messages_arr, prompt , 'user')
        print(f"INITIALIZATION COMPLETE --- " , messages_arr)
        
    else:
        
        print(" NO INITTTTTTILAAIZRION ---- MESSAGES ARRAY. +++++++.++++ + + +" , messages_arr)
        add_message_to_chat(messages_arr, query , 'user')
        
    response = openai.chat.completions.create(
        
        model="gpt-4-turbo",
        messages=messages_arr,
        tools = tools,
        tool_choice = "auto"

    )
    ##print(response.choices[0].message.content)
    if response.choices[0].finish_reason!= 'tool_calls':
        add_message_to_chat(messages_arr, response.choices[0].message.content , 'assistant')
        return response.choices[0].message.content
        
    else:
        
        tool_calls = response.choices[0].message.tool_calls
        
        clean_tool_calls = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in tool_calls
        ]
        
        messages_arr.append({
    "role": "assistant",
    "content": None,
    "tool_calls": clean_tool_calls
})
        
      
        
        
        print("------------ tool called ---------------")
        
       
    

       ## print("message added")

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Handle `convert_to_months`
            if tool_name == 'convert_to_months':
                print("------------ convert to months ---------------")
                converted_value = convert_to_months(
                    current_number=args["current_number"],
                    current_format=args["current_format"]
                )
                tool_answer = f' the conversion of {args["current_number"]} {args["current_format"]} in months is {converted_value}'
                

                # print("Converted to months:", converted_value)

            # Handle `education_ranking`
            elif tool_name == 'education_ranking':
                print("----------- education ranking ---------------")
                edu_map = education_ranking()
                tool_answer = f'use this dictionary regarding the education rankings and thern you you use case statements in SQL  {edu_map}' 
                
                ##print("tool answer is", tool_answer)
                
               
            
            elif tool_name == 'calculate_monthly_payment_with_interest':
                loan_pay = calculate_monthly_payment_with_interest(
                    total_loan_amount=args["loan_amount"],
                    years = args["loan_duration"],
                    duration_string = args["duration_string"],
                    annual_interest_rate=10)
                ##print("Fixed Monthly Payments:", loan_pay)
                
                tool_answer = ("you should give a SQL statement to decide if a customer is eligible for a loan"
            
                f"Amortization formula was applied and resulted in a fixed monthly payment of {loan_pay} per month."

                "RULES TO USE THE SCHEMA TO DECIDE IF A CUSTOMER IS ELIGIBLE FOR A LOAN ARE as follows"
            
                '''
                - you need to find the customer current balance
                
                - you need to find what salary over that period of loan so if the loan is 5 years then the salary per month * 60 months
 
                - you need to find the total customer commitments over that period so get every commitment per month by dividing the (commitmentprice/duration)* number of months for the loan   ( a customer may have more than one commitment)
                
                - new_balance = current_balance + total_salary - total_commitments
                
                - 0.4 MULTIPLIED BY THE NEW BALANCE should be > than the amount to pay per month THAT YOU ALREADY HAVE FROM THE loan_pay variable -- amortization above ) ( THIS RESULT OF THE AMORTIZATION FORMULA SHOULD BE USED)
                
                '''
                )
            
            
                
            elif tool_name == 'clarification_needed':
                print("------------ clarification tool ---------------")
                retrieved_text= args["retrieved_data"]
                tool_answer = clarification_needed(retrieved_text, query)
            
                ##print("tool answer is", tool_answer)
            
            elif tool_name == 'retrieve_stock_data':
                print("------------ retrieve stock data tool ---------------")
                stock_data = retrieve_stock_data(ticker = args["ticker"],
                multiplier = args["multiplier"],
                timespan = args["timespan"],
                from_ = args["from_"],
                to = args["to"])
                
                
                tool_answer = (f"The data retrieved from the API is {stock_data}.")
            
            elif tool_name == 'calculate_max_loan_amount_from_monthly_payment':
                print("------------ max loan amount tool ---------------")
                
                max_loan = calculate_max_loan_amount_from_monthly_payment(years = args["years"],
                duration_string = args["duration_string"],
                monthly_payment = args["monthly_payment"],
                annual_interest_rate = args["annual_interest_rate"])
                
                
                tool_answer = (f"Based on a monthly payment of {args['monthly_payment']} SAR, a loan duration of {args['years']} "
                                f"{args['duration_string']}(s), and an annual interest rate of {args['annual_interest_rate']}%, "
                                f"the customer is eligible for a maximum loan amount of approximately {max_loan} SAR.")
                ##print("tool answer is", tool_answer)
            
                
                
            add_message_to_chat(
            messages_arr,
            message=tool_answer,
            entity="tool",
            function_name=tool_name,
            tool_call_id=tool_call.id
        )
            
           ## print(" ----- the message array after adding the toiol calls ---- ", messages_arr)
        return generate_response('', messages_arr , 0)
                
    

engine = create_engine("postgresql://sondosali:postgres@localhost:5432/AlInma_db")

with open(all_chunks_path, "rb") as f:
    docs = pickle.load(f)
index = faiss.read_index(embeddings_path)

# Query
query = "iPhone"
query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
D, I = index.search(query_embedding, k=10)

retrieved_texts = [docs[i]['text'] for i in I[0]]
for i, text in enumerate(retrieved_texts):
    print(f"[{i}] >>> {text}\n")



 

# Update with your actual DB connection



print(len(docs))




 


app = Flask(__name__)

app.secret_key = 'super_secret_123'  # ✅ Add this line



 

@app.route('/')

def home():

    return render_template('index.html')

 

from flask import flash, redirect, url_for, session, request

 

@app.route('/login', methods=['POST'])

def login():

    email = request.form.get('email')
    password = request.form.get('password')

    print("Login attempt:", email, "---", password)

    user_pass = pd.read_sql(f"SELECT password,customerid from customer_credentials where email = '{email}' ",engine)
   
    if not user_pass.empty and user_pass.iloc[0]['password'] == password:

        customer_id = user_pass.iloc[0]['customerid']
        print("customer  id   >> ", customer_id)
        user_info = pd.read_sql(f"SELECT * from demographics d inner join customer_balances cb on d.customerid = cb.customerid  where d.customerid = '{customer_id}'",engine)
        print ("retrieved user info", user_info)

       
        print("LOG IN SUCCESS")
        session['user'] = email
        return redirect(url_for('chat'))
    else:
        print("Login Failll")
        error = "Invalid email or password"
        return render_template('index.html', error=error)



@app.route('/logout')

def logout():

    session.pop('user', None)

    return redirect(url_for('home'))

 

@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('home'))

    email = session['user']
    query = f"""
        SELECT d.firstname, d.lastname, cb.currentbalance
        FROM demographics d
        INNER JOIN customer_credentials cc ON d.customerid = cc.customerid
        INNER JOIN customer_balances cb ON d.customerid = cb.customerid
        WHERE cc.email = '{email}'
    """
    user_info = pd.read_sql(query, engine)
    if not user_info.empty:
        name = f"{user_info.iloc[0]['firstname']} {user_info.iloc[0]['lastname']}"
        balance = float(user_info.iloc[0]['currentbalance'])
    else:
        name = "User"
        balance = 0.0

    return render_template('chat.html', name=name, balance=balance)





@app.route('/financial-chat')

def financial_chat():

    return render_template('chat1.html')



messages_arr = []

@app.route('/ask2', methods=['POST'])
def ask2():
    global messages_arr

    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "Empty query"}), 400

    def generate():
        response_text = generate_response(query, messages_arr, initialization=len(messages_arr) == 0)
        for char in response_text:
            yield char

    return Response(stream_with_context(generate()), mimetype='text/plain')


 
 

if __name__ == '__main__':

    app.run(debug=True)

