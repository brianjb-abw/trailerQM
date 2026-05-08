import os
from dotenv import load_dotenv

load_dotenv()

f_CB = float(os.environ["CB_FRGT"])
f_CL = float(os.environ["CL_FRGT"])


def get_3pFRates():
    print(f"3rd Party Freight: \nCB:  ${f_CB:10,.2f} \nCL:    ${f_CL:10,.2f}\n")
