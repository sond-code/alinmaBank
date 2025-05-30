
from polygon import RESTClient
import datetime
import faiss
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')



def education_ranking():
    education_arr = ['High School' , 'diploma' , 'bachelors', 'masters' ,'phd']
    
    ranking_dict = {}
    
    for idx , elem in enumerate(education_arr):
        ranking_dict[elem] = idx + 1
    return ranking_dict 
    
print(education_ranking())

def convert_to_months(current_number , current_format):
    
    if current_format in ['day','days']:
        return int(current_number / 30)
        
    elif current_format in('year','years'):
        return int(current_number * 12 )
        
    return current_number

convert_to_months(30,'day')


def clarification_needed(retrieved_data , user_question):

    return "Clarification is needed for the question . Please respond by asking the user for clarification"


def calculate_monthly_payment_with_interest(total_loan_amount, years, duration_string,annual_interest_rate=10):
    
    
    print(" ------ THE MONTHLY PAYMENT FUNCTION WAS CALLED ----- AMORTIZATION ")

    """

    Calculates the monthly payment including interest using amortization formula.

   

    :param total_loan_amount: Total loan amount to be paid

    :param years: Number of years to repay the loan
    
    :param duration_string: if the duration is in years or months 

    :param annual_interest_rate: Annual interest rate (default is 10%)
    
   
    
    :return: Monthly payment including interest

    """

    
    
    if duration_string == 'month' :
        years = years/12
        
    months = years * 12
    monthly_rate = annual_interest_rate / 12 / 100

    if monthly_rate == 0:
        monthly_payment = total_loan_amount / months

    else:
        monthly_payment = (total_loan_amount * monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)


    return round(monthly_payment, 2)


def calculate_max_loan_amount_from_monthly_payment(years, duration_string, monthly_payment = 0, annual_interest_rate=10):
    print(" ------ THE LOAN AMOUNT FUNCTION WAS CALLED ----- REVERSE AMORTIZATION ")
 
    """
    Calculates the total loan amount based on a given monthly payment using the reverse amortization formula.
 
    :param monthly_payment: Monthly payment amount
    :param years: Number of years to repay the loan
    :param duration_string: if the duration is in years or months
    :param annual_interest_rate: Annual interest rate (default is 10%)
    :return: Total loan amount
    """
    # if monthly_payment == 0:
    #     0.4 * (balance - commitments) 
    if duration_string == 'month':
        years = years / 12
    months = years * 12
    monthly_rate = annual_interest_rate / 12 / 100
 
    if monthly_rate == 0:
        total_loan_amount = monthly_payment * months
    else:
        total_loan_amount = (monthly_payment * ((1 + monthly_rate) ** months - 1)) / (monthly_rate * (1 + monthly_rate) ** months)
 
    return round(total_loan_amount, 2)



def retrieve_stock_data(ticker, multiplier, timespan, from_, to):
    
    client = RESTClient(api_key="PXjfh_UtmUvLKP4RgsJ8GPJefT_JiQ7e")

    aggs = []
    result = []

# Example: get AAPL daily price bars between May 1 and May 7, 2024

    aggs = client.get_aggs(
        ticker=ticker,
        multiplier=multiplier,             
        timespan=timespan, 
        from_=from_,
        to=to,
    )

    
    for bar in aggs:
        readeable_date = datetime.datetime.utcfromtimestamp(bar.timestamp/1000)
        result.append(f"Date: {readeable_date}, Open: {bar.open}, High: {bar.high}, Low: {bar.low}, Close: {bar.close}, Volume: {bar.volume}")
        
    # print(result)
    return result


    
# retrieve_stock_data(ticker="AAPL", multiplier=1, timespan="day", from_="2025-05-01", to="2025-05-28")
        
        
tools = [
    {
        "type": "function",
        "function": {
            "name": "convert_to_months",
            "description": "Convert a number in days or years to months.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_number": {"type": "number"},
                    "current_format": {
                        "type": "string",
                        "enum": ["days", "day", "years", "year"]
                    }
                },
                "required": ["current_number", "current_format"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "education_ranking",
        "description": (
            "Returns a dictionary that maps education levels to numeric rankings. "
            "Use this tool to compare education degrees — such as checking if a customer has a degree higher than another. "
            "ALWAYS call this tool when the user mentions words like: bachelor's, diploma, master, PhD, or education level comparison."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
,
    {
      "type": "function",
      "function": {
        "name": "calculate_monthly_payment_with_interest",
        "description": "MUST be called whenever the user question involves requesting loans, fixed monthly payments, annual interest rate in percentage, loans duration and loan total amount, EVERY TIME THE QUESTION IS REGARDING LOAND THEN THIS FUNCITOON STRICLTY NEEDS TO BE CALLED. CALLLL ITTTT .  Do NOT answer without calling this function first.",
        "parameters": {
          "type": "object",
          "properties": {
                    "loan_amount": {"type": "number"},
              
                    "loan_duration": {"type": "number" , 
                                      "description" :  "the loan duration in years"},
              
                    "duration_string": {"type": "string" , 
                                        "description": "wether the duration was given in months or in years." , 
                                        "enum": ["year","month"] 
                                       },
              
                    "annual_interest_rate": {"type": "number"}
              
                },
                "required": ["loan_amount", "loan_duration","duration_string"]
        }
      }
    } 
      ,
     {
        "type": "function",
        "function": {
            "name": "clarification_needed",
             "description": (
                "Use this tool to ask the user for clarification when their question is too vague to answer directly. "
                "ONLY use this tool if the question lacks critical details — such as asking for the price of a product without specifying the model. "
                 "DO NOT CALL THE TOOOL THE USER ASKS ABOUT iphone 12, IPHONE 13 , IPHONE 14 , IPHONE 15 , IPHONE 16 "
                "For example, if the user asks 'What is the price of an iPhone?' without mentioning the specific model (e.g., iPhone 12, iPhone 13, iPhone 15), then call this tool. "
                "However, if the model is  mentioned like iphone 15 or iphone 12 , or any version , DO NOT call this tool."
                "Also use this tool when the user provides an incomplete identity — like mentioning a first name (e.g., 'What are the commitments of Adam?') without a last name."
            ),

            "parameters": {
                "type": "object",
                "properties": {
                
                    "retrieved_data": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "This is the list of RAG-retrieved text chunks to help determine if clarification is needed."
                    },

                    
                    "user_question" : {
                        "type": "string",
                        "description" : "This is the users asked question that you need to determine if it needs clarification or not" 
                    }
      
                } ,
                "required" : ["retrieved_data","user_question"]
            }
        }
    },
    {
      "type": "function",
      "function": {
        "name": "retrieve_stock_data",
        "description": "Uses the Polygon API to retrieve up-to-date stock market data. Call this function whenever the user asks about stock prices, trends, investment insights, or performance of specific stocks over a period of time.",
        "parameters": {
          "type": "object",
          "properties": {
            "ticker": {
              "type": "string",
              "description": "The stock ticker symbol of the company (e.g., 'AAPL' for Apple, 'GOOGL' for Alphabet/Google). This identifies which stock to retrieve data for."
            },
            "multiplier": {
              "type": "number",
              "description": "The size of each time window used to group the stock data. For example, a multiplier of 1 with timespan 'day' means daily data. A multiplier of 5 with timespan 'minute' would mean 5-minute intervals."
            },
            "timespan": {
              "type": "string",
              "description": "The unit of time for each data interval. Common values include 'minute', 'hour', 'day', 'week', 'month', or 'year'. Used with multiplier to define the granularity of the stock data.",
              "enum": ["minute", "hour", "day", "week", "month", "year"]
            },
            "from_": {
              "type": "string",
              "description": "The start date for the stock data in 'YYYY-MM-DD' format. This defines the beginning of the data range you want to retrieve."
            },
            "to": {
              "type": "string",
              "description": "The end date for the stock data in 'YYYY-MM-DD' format. This defines the last day of the data range you want to retrieve."
            }
          },
          "required": ["ticker", "multiplier", "timespan", "from_", "to"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "calculate_max_loan_amount_from_monthly_payment",
        "description": "Uses reverse amortization to calculate the maximum loan amount a customer can afford based on their desired monthly payment, loan duration, and interest rate. Call this function whenever the question asks how much loan someone can afford or what is the total eligible loan amount based on a monthly payment.",
        "parameters": {
          "type": "object",
          "properties": {
            "years": {
              "type": "number",
              "description": "The total number of years over which the customer wants to repay the loan. If the duration is in months, convert it to years accordingly."
            },
            "duration_string": {
              "type": "string",
              "description": "Specifies whether the loan duration is provided in 'year' or 'month'. Used to normalize the time unit before calculation.",
              "enum": ["year", "month"]
            },
            "monthly_payment": {
              "type": "number",
              "description": "The maximum monthly amount the customer can afford to pay toward a loan. This is the key input used to calculate how large a loan they can qualify for."
            },
            "annual_interest_rate": {
              "type": "number",
              "description": "The annual interest rate (as a percentage, e.g., 10 for 10%). Used to calculate compound interest on the loan."
            }
          },
          "required": ["years", "duration_string", "monthly_payment", "annual_interest_rate"]
        }
      }
    }


]
