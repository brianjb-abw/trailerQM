import os
from dotenv import load_dotenv

load_dotenv()

f_CB = float(os.environ["CB_FRGT"])
f_ACM = float(os.environ["ACM_FRGT"])


def get_3pFRates():
    print(f"3rd Party Freight: \nCB:  ${f_CB:10,.2f} \nCL:    ${f_ACM:10,.2f}\n")
