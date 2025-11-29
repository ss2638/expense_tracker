
import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Budget Tracker", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for enhanced visuals
st.markdown("""<style>
h1 { color: #1E3A8A; font-weight: 700; }
[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 600; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { 
    height: 50px; 
    background-color: #F1F5F9; 
    border-radius: 8px 8px 0 0; 
    padding: 0 24px; 
    font-weight: 600;
    color: #1E293B;
}
.stTabs [aria-selected="true"] { 
    background-color: #3B82F6; 
    color: white !important; 
}
.stProgress > div > div > div { background-color: #3B82F6; }
hr { margin: 2rem 0; border-color: #E2E8F0; }
</style>""", unsafe_allow_html=True)

st.title("💳 Credit Card & Budget Tracker")
st.title("� Credit Card & Budget Tracker")

# Function to extract card info and transactions from PDF
def extract_transactions_from_pdf(pdf_file):
    transactions = []
    raw_text = ""
    in_transaction_section = False
    current_year = None
    card_info = {
        'card_name': 'Unknown Card',
        'last_4_digits': '****',
        'statement_date': None,
        'due_date': None,
        'new_balance': 0.0,
        'minimum_payment': 0.0,
        'credit_limit': 0.0,
        'available_credit': 0.0
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                raw_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
                lines = text.split("\n")
                
                # For Apple Card, look for the header structure and parse multiple lines together
                for i, line in enumerate(lines):
                    # Detect card type first - Chase
                    if ("Prime Visa" in line or "PRIME VISA" in line) and card_info['card_name'] == 'Unknown Card':
                        card_info['card_name'] = "Chase Prime Visa"
                    elif ("Chase" in line and "Amazon" in line) and card_info['card_name'] == 'Unknown Card':
                        card_info['card_name'] = "Chase Amazon Card"
                    
                    # Detect card type - Synchrony Bank (Store Cards)
                    if card_info['card_name'] == 'Unknown Card':
                        if "Synchrony Bank" in line or "SYNCHRONY BANK" in line or "synchrony" in line.lower():
                            if "Lowe" in line or "LOWE" in line or "lowes.com" in line:
                                card_info['card_name'] = "Lowe's Synchrony"
                            elif "Amazon" in line:
                                card_info['card_name'] = "Amazon Store Card"
                            elif "PayPal" in line:
                                card_info['card_name'] = "PayPal Credit"
                            else:
                                card_info['card_name'] = "Synchrony Bank"
                    
                    # Detect card type - DCU (Digital Federal Credit Union)
                    if card_info['card_name'] == 'Unknown Card':
                        if "Digital Federal Credit Union" in line or "DCU" in line:
                            if "FREE CHECKING" in line or "Free Checking" in line:
                                card_info['card_name'] = "DCU Free Checking"
                            elif "PRIMARY SAVINGS" in line or "Primary Savings" in line:
                                card_info['card_name'] = "DCU Primary Savings"
                            else:
                                card_info['card_name'] = "DCU"
                    
                    # Detect card type - Barclays
                    if card_info['card_name'] == 'Unknown Card':
                        if "Barclays" in line or "BARCLAYS" in line or "barclays" in line.lower():
                            if "Frontier Airlines" in line:
                                card_info['card_name'] = "Barclays Frontier Airlines"
                            elif "JetBlue" in line:
                                card_info['card_name'] = "Barclays JetBlue"
                            elif "Wyndham" in line:
                                card_info['card_name'] = "Barclays Wyndham Rewards"
                            elif "Aviator" in line:
                                card_info['card_name'] = "Barclays Aviator"
                            else:
                                card_info['card_name'] = "Barclays"
                    
                    # Detect card type - Capital One
                    if card_info['card_name'] == 'Unknown Card':
                        if "Capital One" in line or "CAPITAL ONE" in line or "capitalone" in line.lower():
                            if "VentureOne" in line or "Venture One" in line:
                                card_info['card_name'] = "Capital One VentureOne"
                            elif "Venture X" in line:
                                card_info['card_name'] = "Capital One Venture X"
                            elif "Venture" in line:
                                card_info['card_name'] = "Capital One Venture"
                            elif "Quicksilver" in line:
                                card_info['card_name'] = "Capital One Quicksilver"
                            elif "Savor" in line:
                                card_info['card_name'] = "Capital One Savor"
                            else:
                                card_info['card_name'] = "Capital One"
                    
                    # Detect card type - American Express
                    if card_info['card_name'] == 'Unknown Card':
                        if "American Express" in line or "AMERICAN EXPRESS" in line:
                            # Try to get specific card name
                            if "Cash Magnet" in line:
                                card_info['card_name'] = "American Express Cash Magnet"
                            elif "Gold" in line:
                                card_info['card_name'] = "American Express Gold"
                            elif "Platinum" in line:
                                card_info['card_name'] = "American Express Platinum"
                            elif "Blue Cash" in line:
                                card_info['card_name'] = "American Express Blue Cash"
                            else:
                                card_info['card_name'] = "American Express"
                    
                    # Detect card type - Bank of America
                    if card_info['card_name'] == 'Unknown Card':
                        if "Bank of America" in line or "BANK OF AMERICA" in line:
                            card_info['card_name'] = "Bank of America"
                        elif "BankofAmerica" in line or "BANKOFAMERICA" in line:
                            card_info['card_name'] = "Bank of America"
                        elif "Customized Cash Rewards" in line:
                            card_info['card_name'] = "Bank of America Cash Rewards"
                        elif "Premium Rewards" in line:
                            card_info['card_name'] = "Bank of America Premium Rewards"
                        elif "Travel Rewards" in line:
                            card_info['card_name'] = "Bank of America Travel Rewards"
                    
                    # Detect card type - Apple Card
                    if "Apple Card" in line and "Co-Owners" not in line and "Installments" not in line and card_info['card_name'] == 'Unknown Card':
                        card_info['card_name'] = "Apple Card"
                    
                    # Detect card type - Discover
                    if "DISCOVER" in line.upper() and "CARD ENDING IN" in line.upper() and card_info['card_name'] == 'Unknown Card':
                        card_info['card_name'] = "Discover Card"
                        card_match = re.search(r'ENDING IN\s*(\d{4})', line, re.IGNORECASE)
                        if card_match:
                            card_info['last_4_digits'] = card_match.group(1)
                    
                    # Extract card information - Chase format
                    if "Account Number:" in line and "XXXX" in line:
                        account_match = re.search(r'XXXX XXXX XXXX (\d{4})', line)
                        if account_match:
                            card_info['last_4_digits'] = account_match.group(1)
                            if card_info['card_name'] == 'Unknown Card':
                                card_info['card_name'] = "Chase Card"
                    
                    # Amex: Account Ending
                    if "Account Ending" in line or "Card Ending" in line:
                        # Format: "Account Ending5-05001" or "Card Ending5-05001"
                        amex_match = re.search(r'Ending\s*(\d[-\d]+)', line)
                        if amex_match and card_info['last_4_digits'] == '****':
                            # Extract last 4 or 5 digits
                            acct = amex_match.group(1).replace('-', '')
                            card_info['last_4_digits'] = acct[-4:] if len(acct) >= 4 else acct
                    
                    # Capital One/Barclays: ending in XXXX or Ending5459
                    if ("ending in" in line.lower() or "Ending" in line) and card_info['last_4_digits'] == '****':
                        # Try "ending in 6165" format
                        cap1_match = re.search(r'ending in\s*(\d{4})', line, re.IGNORECASE)
                        if cap1_match:
                            card_info['last_4_digits'] = cap1_match.group(1)
                        else:
                            # Try "Ending5459" format (no space)
                            barclays_match = re.search(r'Ending\s*(\d{4})', line)
                            if barclays_match:
                                card_info['last_4_digits'] = barclays_match.group(1)
                    
                    # DCU: ACCT# X
                    if "ACCT#" in line and card_info['last_4_digits'] == '****':
                        dcu_match = re.search(r'ACCT#\s*(\d+)', line)
                        if dcu_match:
                            acct_num = dcu_match.group(1)
                            card_info['last_4_digits'] = acct_num if len(acct_num) <= 4 else acct_num[-4:]
                    
                    # Synchrony: Account Number ending in XXX
                    if "Account Number ending in" in line and card_info['last_4_digits'] == '****':
                        # Pattern: "Account Number ending in 698 0" - may have space in the number
                        sync_match = re.search(r'ending in\s*([\d\s]+)', line, re.IGNORECASE)
                        if sync_match:
                            acct_num = sync_match.group(1).replace(' ', '').strip()
                            card_info['last_4_digits'] = acct_num if len(acct_num) <= 4 else acct_num[-4:]
                    
                    # Chase/Amex/Capital One/Barclays/Synchrony: Payment Due Date
                    if ("Payment Due Date" in line or "Payment Due:" in line) and not card_info['due_date']:
                        # Try various formats
                        # Format 1: MM/DD/YYYY (Synchrony, some Discover) - check this FIRST
                        due_match_yyyy = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                        if due_match_yyyy:
                            try:
                                card_info['due_date'] = pd.to_datetime(due_match_yyyy.group(1), format='%m/%d/%Y')
                            except:
                                pass
                        
                        # Format 2: "Nov 04, 2025" (Capital One)
                        if not card_info['due_date']:
                            due_match_word = re.search(r'(\w{3}\s+\d{1,2},\s+\d{4})', line)
                            if due_match_word:
                                try:
                                    card_info['due_date'] = pd.to_datetime(due_match_word.group(1), format='%b %d, %Y')
                                except:
                                    pass
                        
                        # Format 3: MM/DD/YY (2-digit year) - LAST resort
                        if not card_info['due_date']:
                            due_match_yy = re.search(r'(\d{1,2}/\d{1,2}/\d{2})(?!\d)', line)
                            if due_match_yy:
                                try:
                                    card_info['due_date'] = pd.to_datetime(due_match_yy.group(1), format='%m/%d/%y')
                                except:
                                    pass
                    
                    # Legacy check for "due date" (lowercase) - for other formats
                    if "due date" in line.lower() and "Payment Due Date" not in line and not card_info['due_date']:
                        # Try MM/DD/YY format for legacy cards
                        due_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2})(?!\d)', line)
                        if due_match:
                            try:
                                card_info['due_date'] = pd.to_datetime(due_match.group(1), format='%m/%d/%y')
                            except:
                                pass
                    
                    # DCU: NEW BALANCE (statement balance)
                    if "NEW BALANCE" in line and "$" not in line and card_info['new_balance'] == 0.0:
                        # Look for balance on same line or parse the number
                        balance_match = re.search(r'([\d,]+\.\d{2})', line)
                        if balance_match:
                            card_info['new_balance'] = float(balance_match.group(1).replace(',', ''))
                    
                    # Synchrony: New Balance with colon
                    if "New Balance:" in line and "$" in line and card_info['new_balance'] == 0.0:
                        balance_match = re.search(r'\$[\d,]+\.\d{2}', line)
                        if balance_match:
                            card_info['new_balance'] = float(balance_match.group().replace('$', '').replace(',', ''))
                    
                    # Chase/Amex/Barclays: New Balance or Statement Balance
                    if ("New Balance" in line or "Statement Balance" in line) and "$" in line:
                        # Look for pattern like "New Balance $994.09" or "Statement Balance: $4.27"
                        balance_match = re.search(r'\$[\d,]+\.\d{2}', line)
                        if balance_match and card_info['new_balance'] == 0.0:
                            # Make sure this isn't from a reward balance, miles, or "as of" date line
                            if "Reward" not in line and "Point" not in line and "Mile" not in line and "as of" not in line.lower():
                                card_info['new_balance'] = float(balance_match.group().replace('$', '').replace(',', ''))
                    
                    # Chase/BofA/Amex/Barclays/Synchrony: Minimum Payment Due
                    if ("Minimum Payment Due" in line or "Minimum payment due" in line.lower() or "Minimum Payment:" in line or "Total Minimum Payment Due:" in line) and "$" in line:
                        min_match = re.search(r'\$[\d,]+\.\d{2}', line)
                        if min_match and card_info['minimum_payment'] == 0.0:
                            card_info['minimum_payment'] = float(min_match.group().replace('$', '').replace(',', ''))
                    
                    # Alternative: "Minimum Payment" without "Due"
                    if "Minimum Payment" in line and "Due:" not in line and "Warning" not in line and "$" in line and card_info['minimum_payment'] == 0.0:
                        min_match = re.search(r'\$[\d,]+\.\d{2}', line)
                        if min_match:
                            card_info['minimum_payment'] = float(min_match.group().replace('$', '').replace(',', ''))
                    
                    # Chase: Credit Access Line
                    if "Credit Access Line" in line and "Available" not in line:
                        credit_match = re.search(r'\$[\d,]+', line)
                        if credit_match and card_info['credit_limit'] == 0.0:
                            card_info['credit_limit'] = float(credit_match.group().replace('$', '').replace(',', ''))
                    
                    # Amex/Capital One/Barclays/Synchrony: Credit Limit or Credit Line
                    # Must check this BEFORE available credit to avoid confusion
                    if "Credit Limit" in line and "$" in line and "Cash Advance" not in line:
                        # Match the FIRST dollar amount (which is the Credit Limit, not Available Credit)
                        # Pattern: "Credit Limit $9,000 Available Credit $8,882"
                        credit_match = re.search(r'Credit Limit\s+\$?([\d,]+(?:\.\d{2})?)', line, re.IGNORECASE)
                        if credit_match and card_info['credit_limit'] == 0.0:
                            card_info['credit_limit'] = float(credit_match.group(1).replace(',', ''))
                    elif "Credit Line" in line and "$" in line and "Available" not in line and "Cash Advance" not in line:
                        # Try with decimals first
                        credit_match = re.search(r'\$[\d,]+\.\d{2}', line)
                        if not credit_match:
                            # Try without decimals
                            credit_match = re.search(r'\$[\d,]+', line)
                        if credit_match and card_info['credit_limit'] == 0.0:
                            card_info['credit_limit'] = float(credit_match.group().replace('$', '').replace(',', ''))
                    
                    # Chase: Opening/Closing Date
                    if "Opening/Closing Date" in line:
                        date_match = re.search(r'(\d{2}/\d{2}/\d{2})\s*-\s*(\d{2}/\d{2}/\d{2})', line)
                        if date_match and not card_info['statement_date']:
                            try:
                                card_info['statement_date'] = pd.to_datetime(date_match.group(2), format='%m/%d/%y')
                            except:
                                pass
                    
                    # Amex: Closing Date
                    if "Closing Date" in line and not card_info['statement_date']:
                        # Format: "Closing Date11/13/25"
                        date_match = re.search(r'(\d{2}/\d{2}/\d{2})', line)
                        if date_match:
                            try:
                                card_info['statement_date'] = pd.to_datetime(date_match.group(1), format='%m/%d/%y')
                            except:
                                pass
                    
                    # Capital One/Barclays/DCU/Synchrony: Statement date range
                    if not card_info['statement_date']:
                        # Format: "Sep 10, 2025 - Oct 10, 2025"
                        if re.search(r'\w{3}\s+\d{1,2},\s+\d{4}\s*-\s*\w{3}\s+\d{1,2},\s+\d{4}', line):
                            date_match = re.search(r'-\s*(\w{3}\s+\d{1,2},\s+\d{4})', line)
                            if date_match:
                                try:
                                    card_info['statement_date'] = pd.to_datetime(date_match.group(1), format='%b %d, %Y')
                                except:
                                    pass
                        # Format: "10/16/25 - 11/15/25" (Barclays)
                        elif re.search(r'\d{1,2}/\d{1,2}/\d{2}\s*-\s*\d{1,2}/\d{1,2}/\d{2}', line):
                            date_match = re.search(r'-\s*(\d{1,2}/\d{1,2}/\d{2})', line)
                            if date_match:
                                try:
                                    card_info['statement_date'] = pd.to_datetime(date_match.group(1), format='%m/%d/%y')
                                except:
                                    pass
                        # Format: "10-01-25 to 10-31-25" (DCU)
                        elif re.search(r'\d{1,2}-\d{1,2}-\d{2}\s+to\s+\d{1,2}-\d{1,2}-\d{2}', line):
                            date_match = re.search(r'to\s+(\d{1,2}-\d{1,2}-\d{2})', line)
                            if date_match:
                                try:
                                    card_info['statement_date'] = pd.to_datetime(date_match.group(1), format='%m-%d-%y')
                                except:
                                    pass
                        # Format: "as of 11/12/2025" (Synchrony)
                        elif "as of" in line.lower() and re.search(r'\d{1,2}/\d{1,2}/\d{4}', line):
                            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                            if date_match:
                                try:
                                    card_info['statement_date'] = pd.to_datetime(date_match.group(1), format='%m/%d/%Y')
                                except:
                                    pass
                    
                    # Apple Card: Special handling for balance/payment header
                    if "Your" in line and "Balance" in line and "Minimum Payment" in line:
                        # Look for the line with dollar amounts within next few lines
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j]
                            # Find line with dollar amounts
                            amounts = re.findall(r'\$[\d,]+\.\d{2}', next_line)
                            if len(amounts) >= 2:
                                # First amount is balance, second is minimum payment
                                try:
                                    if card_info['new_balance'] == 0.0:
                                        card_info['new_balance'] = float(amounts[0].replace('$', '').replace(',', ''))
                                    if card_info['minimum_payment'] == 0.0:
                                        card_info['minimum_payment'] = float(amounts[1].replace('$', '').replace(',', ''))
                                except:
                                    pass
                    
                    # Apple Card: Look for "Payment Due By" - this is the actual due date!
                    # This should ALWAYS override any other date found (like "as of" dates)
                    if "Due By" in line or ("Payment" in line and "Due" in line):
                        # Look for date in this line or next few lines
                        for j in range(i, min(i+3, len(lines))):
                            check_line = lines[j]
                            # Skip lines with "as of" - those are statement dates, not due dates
                            if "as of" in check_line.lower():
                                continue
                            
                            due_match = re.search(r'(\w{3}\s+\d{1,2},\s+\d{4})', check_line)
                            if due_match:
                                try:
                                    parsed_date = pd.to_datetime(due_match.group(1), format='%b %d, %Y')
                                    # Payment due dates should be in the future or very recent (within last 3 days)
                                    today = pd.Timestamp.now().normalize()
                                    if parsed_date >= today - pd.Timedelta(days=3):
                                        # Unconditionally set - this is the actual due date
                                        card_info['due_date'] = parsed_date
                                        break
                                except:
                                    pass
                    
                    # Discover Card: Look for the payment information section
                    # Pattern: "NewBalance MinimumPayment PaymentDueDate" on one line
                    # followed by "$516.16 $35.00 12/09/2025" on another line
                    if "NewBalance" in line and "MinimumPayment" in line and "PaymentDueDate" in line:
                        # Look in the next few lines for the values
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j]
                            # Look for pattern with 2 dollar amounts and a date
                            amounts = re.findall(r'\$[\d,]+\.\d{2}', next_line)
                            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_line)
                            
                            if len(amounts) >= 2:
                                try:
                                    if card_info['new_balance'] == 0.0:
                                        card_info['new_balance'] = float(amounts[0].replace('$', '').replace(',', ''))
                                    if card_info['minimum_payment'] == 0.0:
                                        card_info['minimum_payment'] = float(amounts[1].replace('$', '').replace(',', ''))
                                except:
                                    pass
                            
                            if date_match and not card_info['due_date']:
                                try:
                                    card_info['due_date'] = pd.to_datetime(date_match.group(1), format='%m/%d/%Y')
                                except:
                                    pass
                    
                    # Discover: CreditLine
                    if "CreditLine" in line and "$" in line and "Available" not in line:
                        credit_match = re.search(r'\$[\d,]+', line)
                        if credit_match and card_info['credit_limit'] == 0.0:
                            card_info['credit_limit'] = float(credit_match.group().replace('$', '').replace(',', ''))
                    
                    # Detect transaction sections
                    if "PAYMENTS AND OTHER CREDITS" in line or "PURCHASE" in line or "CASH ADVANCES" in line:
                        in_transaction_section = True
                        continue
                    
                    if "PAYMENTSANDCREDITS" in line.replace(" ", ""):  # Discover format
                        in_transaction_section = True
                        continue
                    
                    if "PURCHASES" in line and "TRANS." in line:  # Discover format
                        in_transaction_section = True
                        continue
                    
                    if "Transactions by" in line:  # Apple Card format
                        in_transaction_section = True
                        continue
                    
                    if "Payments" in line and ("made by" in line or "Payments made by" in line):  # Apple Card payments
                        in_transaction_section = True
                        continue
                    
                    # Amex format - New Charges section
                    if "New Charges" in line:
                        in_transaction_section = True
                        continue
                    
                    # Amex format - Payments and Credits section
                    if "Payments and Credits" in line and "Summary" not in lines[i-1] if i > 0 else False:
                        in_transaction_section = True
                        continue
                    
                    # Capital One/Barclays/DCU/Synchrony format - Transactions section
                    # Look for "Transactions" header or the column headers
                    if ("Transactions" in line and "Total" not in line and "see" not in line.lower()) or ("Trans Date" in line and "Post Date" in line and "Description" in line) or ("Transaction Date" in line and "Posting Date" in line and "Description" in line) or ("DATE" in line and "TRANSACTION DESCRIPTION" in line and "WITHDRAWALS" in line and "DEPOSITS" in line) or ("Transaction Detail" in line) or ("Date" in line and "Reference Number" in line and "Description" in line and "Amount" in line):
                        in_transaction_section = True
                        continue
                    
                    # Stop at certain sections
                    if "2025 Totals Year-to-Date" in line or "INTEREST CHARGES" in line or "Apple Card Monthly Installments" in line or "Daily Cash" in line:
                        in_transaction_section = False
                        continue
                    
                    if "FeesandInterestCharged" in line or "Fees and Interest Charged" in line or "TOTALS YEAR-TO-DATE" in line:
                        in_transaction_section = False
                        continue
                    
                    # Amex: Stop at Fees section
                    if line.strip() == "Fees" or line.strip() == "Interest Charged" or "Continued on reverse" in line:
                        in_transaction_section = False
                        continue
                    
                    # Capital One: Stop at summary sections
                    if "Total Transactions for This Period" in line or "Total Fees for This Period" in line or "Total Interest for This Period" in line or "DEPOSITS, DIVIDENDS AND OTHER CREDITS" in line or "WITHDRAWALS, FEES AND OTHER DEBITS" in line or "S T A T E M E N T  S U M M A R Y" in line or "Total Fees Charged This Period" in line or "Total Interest Charged This Period" in line or "2025 Year- to- Date Fees and Interest" in line:
                        in_transaction_section = False
                        continue
                    
                    # Extract year from statement
                    year_match = re.search(r'(December|November|October|September|August|July|June|May|April|March|February|January)\s+(\d{4})', line)
                    if year_match:
                        current_year = year_match.group(2)
                    
                    # Extract year from Capital One statement header
                    cap1_year_match = re.search(r'(\w{3})\s+\d{1,2},\s+(\d{4})\s*-\s*\w{3}\s+\d{1,2},\s+(\d{4})', line)
                    if cap1_year_match:
                        current_year = cap1_year_match.group(3)  # Use the ending year
                    
                    # Extract year from Apple Card statement header
                    apple_date_match = re.search(r'(\w{3})\s+\d{1,2}\s*—\s*\w{3}\s+\d{1,2},\s*(\d{4})', line)
                    if apple_date_match:
                        current_year = apple_date_match.group(2)
                    
                    if in_transaction_section:
                        # Synchrony format: 10/28 70556 STORE 0678 CUMMING GA $19.98
                        # Date Reference# Description Amount
                        match_sync = re.match(r'^(\d{1,2}/\d{1,2})\s+(\d+\s+)?(.+?)\s+(\-?\$[\d,]+\.\d{2})\s*$', line.strip())
                        
                        # DCU format: OCT02 EFT ACH AMEX EPAYMENT ACH PMT 251002 Raj DCU -402.53 9,278.35
                        # DATE TRANSACTION DESCRIPTION WITHDRAWALS DEPOSITS BALANCE
                        # Pattern: MMMDD Description [optional withdrawal] [optional deposit] Balance
                        match_dcu = re.match(r'^([A-Z]{3})(\d{2})\s+(.+?)\s+([-]?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$', line.strip())
                        
                        # Barclays format: Nov 10 Nov 12 HOBBY-LOBBY #0231 CUMMING GA 4 $4.27
                        # Transaction Date Posting Date Description Miles Amount
                        # Pattern: Month Day Month Day Description [optional miles/points] $Amount
                        match_barclays = re.match(r'^([A-Z][a-z]{2})\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{1,2})\s+(.+?)\s+(\d+\s+)?(\-?\$[\d,]+\.\d{2})\s*$', line.strip())
                        
                        # Capital One format: Oct 2 Oct 4 ETIHAD AIRWAYSMUMBAIMAH $925.81
                        # Trans Date Post Date Description Amount
                        # Pattern: Month Day Month Day Description $Amount
                        match_cap1 = re.match(r'^([A-Z][a-z]{2})\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{1,2})\s+(.+?)\s+(\-?\$[\d,]+\.\d{2})\s*$', line.strip())
                        
                        # Amex format: MM/DD/YY Description $Amount
                        # Example: "10/28/25 GOOGLE *YOUTUBEPREMIUM G.CO/HELPPAY# CA $22.99"
                        match_amex = re.match(r'^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(\-?\$?[\d,]+\.\d{2})$', line.strip())
                        
                        # Chase format: MM/DD Description Amount
                        match_chase = re.match(r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\d+\.\d{2})$', line.strip())
                        
                        # Apple Card format: MM/DD/YYYY Description Daily Cash% $X.XX $Amount
                        match_apple = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+\d+%\s+\$?[\d.]+\s+([-]?\$?[\d,]+\.\d{2})$', line.strip())
                        
                        # Apple Card payment format: MM/DD/YYYY Description -$Amount
                        match_apple_payment = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-]\$?[\d,]+\.\d{2})$', line.strip())
                        
                        # Discover format: MM/DD Description Category/Location $Amount or -$Amount
                        # Example: "10/13 PAYPAL *WALMART COM WAL 888-221-1161 Supermarkets $42.76"
                        match_discover = re.match(r'^(\d{2}/\d{2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})$', line.strip())
                        
                        if match_sync:
                            date_str = match_sync.group(1)  # 10/28
                            # Group 2 is optional reference number
                            description = match_sync.group(3).strip()
                            amount_str = match_sync.group(4).replace('$', '').replace(',', '')
                            
                            try:
                                # Use current year or statement year
                                year = current_year if current_year else "2025"
                                full_date_str = f"{date_str}/{year}"
                                date = pd.to_datetime(full_date_str, format='%m/%d/%Y')
                                
                                # Synchrony shows purchases as positive, payments/credits as negative
                                # Convert purchases to negative (expenses), keep payments positive
                                amount = float(amount_str)
                                if amount > 0 and "PAYMENT" not in description.upper() and "CREDIT" not in description.upper() and "THANK YOU" not in description.upper():
                                    amount = -amount
                                
                                # Skip section headers and summary lines
                                skip_keywords = ["Payments", "Other Credits", "Purchases and Other Debits", "Total", "Invoice Number"]
                                if not any(keyword in description for keyword in skip_keywords):
                                    # Clean up description - remove store numbers and extra details
                                    description = re.sub(r'STORE\s+\d+', '', description)
                                    description = re.sub(r'\s+[A-Z]{2}$', '', description)  # Remove state codes at end
                                    description = re.sub(r'^-,\s*-\s*', '', description)  # Remove "-, -" prefixes
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_dcu:
                            month_abbr = match_dcu.group(1)  # OCT
                            day = match_dcu.group(2)         # 02
                            description = match_dcu.group(3).strip()
                            amount_or_withdrawal = match_dcu.group(4)  # Could be withdrawal or deposit
                            balance = match_dcu.group(5)
                            
                            try:
                                # Convert month abbreviation to number
                                month_map = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                                           'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
                                month_num = month_map.get(month_abbr, '01')
                                
                                # Use current year or statement year
                                year = current_year if current_year else "2025"
                                date_str = f"{month_num}/{day}/{year}"
                                date = pd.to_datetime(date_str, format='%m/%d/%Y')
                                
                                # Parse amount - negative means withdrawal (expense), positive means deposit (income)
                                amount = float(amount_or_withdrawal.replace(',', ''))
                                
                                # Skip certain transactions
                                skip_keywords = ["PREVIOUS BALANCE", "NEW BALANCE", "DIVIDEND", "ANNUAL PERCENTAGE"]
                                if not any(keyword in description.upper() for keyword in skip_keywords):
                                    # Clean up description
                                    description = re.sub(r'\s+\d{6}\s+', ' ', description)  # Remove date stamps like 251002
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_barclays:
                            trans_month = match_barclays.group(1)  # Nov
                            trans_day = match_barclays.group(2)    # 10
                            post_month = match_barclays.group(3)   # Nov
                            post_day = match_barclays.group(4)     # 12
                            description = match_barclays.group(5).strip()
                            # Group 6 is optional miles/points, group 7 is amount
                            amount_str = match_barclays.group(7).replace('$', '').replace(',', '')
                            
                            try:
                                # Use transaction date for the record
                                year = current_year if current_year else "2025"
                                trans_date_str = f"{trans_month} {trans_day} {year}"
                                date = pd.to_datetime(trans_date_str, format='%b %d %Y')
                                
                                # Barclays shows purchases as positive, payments as negative
                                # Convert purchases to negative (expenses)
                                amount = float(amount_str)
                                if amount > 0 and "PAYMENT" not in description.upper() and "CREDIT" not in description.upper():
                                    amount = -amount
                                
                                # Skip summary lines and headers
                                skip_keywords = ["Total", "card ending", "for this period", "No Payment", "No fees", "No interest"]
                                if not any(keyword in description for keyword in skip_keywords):
                                    # Clean up description - remove location codes
                                    description = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', description)
                                    description = re.sub(r'\s+[A-Z]{2}\s+USA$', '', description)
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_cap1:
                            trans_month = match_cap1.group(1)  # Oct
                            trans_day = match_cap1.group(2)    # 2
                            post_month = match_cap1.group(3)   # Oct
                            post_day = match_cap1.group(4)     # 4
                            description = match_cap1.group(5).strip()
                            amount_str = match_cap1.group(6).replace('$', '').replace(',', '')
                            
                            try:
                                # Use transaction date for the record
                                year = current_year if current_year else "2025"
                                trans_date_str = f"{trans_month} {trans_day} {year}"
                                date = pd.to_datetime(trans_date_str, format='%b %d %Y')
                                
                                # Capital One shows purchases as positive, payments as negative
                                # Convert purchases to negative (expenses)
                                amount = float(amount_str)
                                if amount > 0 and "PAYMENT" not in description.upper() and "CREDIT" not in description.upper():
                                    amount = -amount
                                
                                # Skip lines with card holder names, totals, exchange rates, and currency codes
                                skip_keywords = ["#", "Total", "Exchange Rate", "INR", "USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
                                if not any(keyword in description for keyword in skip_keywords):
                                    # Clean up description - remove location codes and phone numbers
                                    description = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', description)
                                    description = re.sub(r'\s+[A-Z]{2}\s+USA$', '', description)
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_amex:
                            date_str = match_amex.group(1)
                            description = match_amex.group(2).strip()
                            amount_str = match_amex.group(3).replace('$', '').replace(',', '')
                            
                            try:
                                date = pd.to_datetime(date_str, format='%m/%d/%y')
                                
                                # Amex shows purchases as positive, payments as negative
                                # Convert purchases to negative (expenses)
                                amount = float(amount_str)
                                if amount > 0:
                                    amount = -amount
                                
                                # Skip summary lines and section headers
                                if "Total" not in description and "Summary" not in description and "Detail" not in description and "Card Ending" not in description:
                                    # Clean up description
                                    description = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', description)
                                    description = re.sub(r'\s+\d{5,}', '', description)
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_chase and not match_discover:
                            date_str = match_chase.group(1)
                            description = match_chase.group(2).strip()
                            amount_str = match_chase.group(3)
                            
                            try:
                                year = current_year if current_year else "2025"
                                full_date_str = f"{date_str}/{year}"
                                date = pd.to_datetime(full_date_str, format='%m/%d/%Y')
                                amount = float(amount_str)
                                
                                if "Order Number" not in description:
                                    transactions.append([date, description, amount])
                            except Exception as e:
                                continue
                        
                        elif match_discover:
                            date_str = match_discover.group(1)
                            description = match_discover.group(2).strip()
                            amount_str = match_discover.group(3).replace('$', '').replace(',', '')
                            
                            try:
                                year = current_year if current_year else "2025"
                                full_date_str = f"{date_str}/{year}"
                                date = pd.to_datetime(full_date_str, format='%m/%d/%Y')
                                
                                # Discover shows payments as negative, purchases as positive
                                # We want expenses as negative, so negate if positive
                                amount = float(amount_str)
                                if amount > 0 and "PAYMENT" not in description.upper() and "THANK YOU" not in description.upper():
                                    amount = -amount  # Convert purchases to negative
                                
                                # Clean up description - remove phone numbers and extra location codes
                                description = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', description)
                                description = re.sub(r'\s+\d{5,}', '', description)
                                description = re.sub(r'\s+(CA|NY|TX|FL|GA|IL|PA|OH|NC|MI|NJ|VA|WA|AZ|MA|TN|IN|MO|MD|WI|CO|MN|SC|AL|LA|KY|OR|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|NH|ME|MT|RI|DE|SD|ND|AK|VT|WY)\s*$', '', description)
                                
                                transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_apple:
                            date_str = match_apple.group(1)
                            description = match_apple.group(2).strip()
                            amount_str = match_apple.group(3).replace('$', '').replace(',', '')
                            
                            try:
                                date = pd.to_datetime(date_str, format='%m/%d/%Y')
                                # Apple Card shows charges as positive, so make them negative for consistency
                                amount = -abs(float(amount_str))
                                
                                # Clean up description - remove extra location info
                                if description:
                                    # Remove state/country codes and extra info
                                    description = re.sub(r'\s+\d{5,}\s+[A-Z]{2}\s+USA$', '', description)
                                    description = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', description)
                                    transactions.append([date, description.strip(), amount])
                            except Exception as e:
                                continue
                        
                        elif match_apple_payment:
                            date_str = match_apple_payment.group(1)
                            description = match_apple_payment.group(2).strip()
                            amount_str = match_apple_payment.group(3).replace('$', '').replace(',', '')
                            
                            try:
                                date = pd.to_datetime(date_str, format='%m/%d/%Y')
                                amount = float(amount_str)  # Already negative
                                
                                transactions.append([date, description, amount])
                            except Exception as e:
                                continue
    
    if not transactions:
        st.warning("⚠️ No transactions found in the PDF. Showing raw text for debugging:")
        with st.expander("View PDF Content"):
            st.text_area("PDF Content", raw_text, height=300)
        return None, card_info
    
    # If we have Apple Card but no last 4 digits extracted, use a placeholder
    if card_info['card_name'] == "Apple Card" and card_info['last_4_digits'] == '****':
        # Try to extract from email or use a generic identifier
        card_info['last_4_digits'] = 'AAPL'
    
    df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount"])
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')
    df = df.dropna(subset=["Date", "Amount"])
    df = df.sort_values('Date').reset_index(drop=True)
    
    return df, card_info

# Categorization function
def categorize(description):
    description = description.lower()
    
    # Shopping
    if "amazon" in description or "shopping" in description or "mall" in description:
        return "Shopping"
    # Food & Groceries
    elif any(word in description for word in ["grocery", "supermarket", "whole foods", "trader joe", "safeway", "kroger", "food", "restaurant", "cafe", "starbucks", "mcdonald", "chipotle"]):
        return "Food & Dining"
    # Housing
    elif any(word in description for word in ["rent", "lease", "mortgage", "apartment"]):
        return "Housing"
    # Transportation
    elif any(word in description for word in ["uber", "lyft", "taxi", "gas", "fuel", "parking", "transit", "commute"]):
        return "Transportation"
    # Entertainment
    elif any(word in description for word in ["netflix", "hulu", "spotify", "movie", "theater", "gaming", "entertainment"]):
        return "Entertainment"
    # Bills & Utilities
    elif any(word in description for word in ["electric", "water", "internet", "phone", "utility", "bill", "insurance"]):
        return "Bills & Utilities"
    # Income & Payments
    elif any(word in description for word in ["salary", "payroll", "payment thank you", "refund", "deposit"]):
        return "Income/Payments"
    else:
        return "Other"

# Upload Multiple PDFs
st.sidebar.header("📄 Upload Statements")
uploaded_pdfs = st.sidebar.file_uploader("Upload credit card statements (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_pdfs:
    all_transactions = []
    all_card_info = []
    
    for pdf_file in uploaded_pdfs:
        with st.spinner(f"Processing: {pdf_file.name}..."):
            df_temp, card_info = extract_transactions_from_pdf(pdf_file)
            if df_temp is not None and len(df_temp) > 0:
                df_temp['Card'] = f"{card_info['card_name']} (...{card_info['last_4_digits']})"
                df_temp['Card_Last4'] = card_info['last_4_digits']
                all_transactions.append(df_temp)
                all_card_info.append({**card_info, 'filename': pdf_file.name})
    
    if all_transactions:
        # Combine all dataframes
        df = pd.concat(all_transactions, ignore_index=True)
        
        # Detect and remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['Date', 'Description', 'Amount', 'Card_Last4'], keep='first')
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            st.sidebar.success(f"✅ Removed {duplicates_removed} duplicate(s)")
        
        # Add categories
        df["Category"] = df["Description"].apply(categorize)
        df = df.sort_values('Date').reset_index(drop=True)
        
        st.sidebar.success(f"✅ Loaded {len(df)} unique transactions from {len(all_card_info)} statement(s)")
        
        # Debug info for card detection
        with st.expander("🔍 Debug: Card Detection Info"):
            for idx, info in enumerate(all_card_info):
                st.write(f"**Statement {idx+1}: {info['filename']}**")
                st.json(info)
    else:
        st.info("Using sample data since no transactions were extracted.")
        df = pd.DataFrame({
            "Date": pd.date_range(start="2025-01-01", periods=10),
            "Description": ["Grocery Store", "Rent Payment", "Netflix", "Uber Ride", "Electric Bill", "Salary", "Shopping Mall", "Water Bill", "Grocery Store", "Amazon"],
            "Amount": [-50, -1200, -15, -20, -100, 3000, -200, -80, -40, -150],
            "Card": ["Sample Card"] * 10,
            "Card_Last4": ["0000"] * 10
        })
        df["Category"] = df["Description"].apply(categorize)
        all_card_info = []
else:
    st.info("👈 Upload your credit card statements to get started!")
    df = pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=10),
        "Description": ["Grocery Store", "Rent Payment", "Netflix", "Uber Ride", "Electric Bill", "Salary", "Shopping Mall", "Water Bill", "Grocery Store", "Amazon"],
        "Amount": [-50, -1200, -15, -20, -100, 3000, -200, -80, -40, -150],
        "Card": ["Sample Card"] * 10,
        "Card_Last4": ["0000"] * 10
    })
    df["Category"] = df["Description"].apply(categorize)
    all_card_info = []

# Credit Card Summary Section
if all_card_info:
    st.header("💳 Credit Card Overview")
    
    # Calculate days until due date
    today = pd.Timestamp.now()
    
    cols = st.columns(len(all_card_info))
    for idx, (col, card) in enumerate(zip(cols, all_card_info)):
        with col:
            days_until_due = (card['due_date'] - today).days if card['due_date'] else None
            
            st.markdown(f"### {card['card_name']}")
            st.markdown(f"**Card ending in:** {card['last_4_digits']}")
            
            if card['due_date']:
                if days_until_due is not None:
                    if days_until_due < 0:
                        st.error(f"⚠️ **OVERDUE by {abs(days_until_due)} days!**")
                    elif days_until_due <= 3:
                        st.error(f"🚨 **Due in {days_until_due} days!**")
                    elif days_until_due <= 7:
                        st.warning(f"⏰ Due in {days_until_due} days")
                    else:
                        st.info(f"📅 Due in {days_until_due} days")
                    
                    st.markdown(f"**Due Date:** {card['due_date'].strftime('%m/%d/%Y')}")
            
            st.metric("Balance", f"${card['new_balance']:,.2f}")
            st.metric("Min Payment", f"${card['minimum_payment']:,.2f}")
            
            if card['credit_limit'] > 0:
                utilization = (card['new_balance'] / card['credit_limit']) * 100
                st.metric("Credit Utilization", f"{utilization:.1f}%")
                st.progress(min(utilization / 100, 1.0))
                
                if utilization > 90:
                    st.error("⚠️ High utilization!")
                elif utilization > 30:
                    st.warning("⚠️ Consider paying down")
    
    st.divider()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Automatically detect date range from transactions
valid_dates = df["Date"].dropna()
if len(valid_dates) > 0:
    auto_start = valid_dates.min().date()
    auto_end = valid_dates.max().date()
    date_range_days = (auto_end - auto_start).days
    st.sidebar.info(f"📅 **Auto-detected range:** {date_range_days + 1} days\n\n{auto_start.strftime('%b %d, %Y')} → {auto_end.strftime('%b %d, %Y')}")
else:
    auto_start = pd.Timestamp.now().date()
    auto_end = pd.Timestamp.now().date()

start_date = st.sidebar.date_input("Start Date", auto_start)
end_date = st.sidebar.date_input("End Date", auto_end)
category_filter = st.sidebar.multiselect("Categories", df["Category"].unique(), default=df["Category"].unique())

# Card filter
if 'Card' in df.columns:
    card_filter = st.sidebar.multiselect("Cards", df["Card"].unique(), default=df["Card"].unique())
else:
    card_filter = []

# Apply filters
filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
filtered_df = filtered_df[filtered_df["Category"].isin(category_filter)]
if card_filter and 'Card' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Card"].isin(card_filter)]

# Summary Metrics - Enhanced
st.header("📊 Financial Overview")

# Calculate metrics
total_income = filtered_df[filtered_df["Amount"] > 0]["Amount"].sum()
total_expenses = abs(filtered_df[filtered_df["Amount"] < 0]["Amount"].sum())
net_balance = total_income - total_expenses
transaction_count = len(filtered_df)

# Calculate additional insights
expenses_df_temp = filtered_df[filtered_df["Amount"] < 0].copy()
if not expenses_df_temp.empty:
    avg_daily_spending = abs(expenses_df_temp.groupby("Date")["Amount"].sum().mean())
    largest_expense = abs(expenses_df_temp["Amount"].min())
    days_in_period = (filtered_df["Date"].max() - filtered_df["Date"].min()).days + 1
    projected_monthly = (total_expenses / days_in_period) * 30 if days_in_period > 0 else 0
else:
    avg_daily_spending = 0
    largest_expense = 0
    days_in_period = 0
    projected_monthly = 0

# Display metrics in a modern card layout
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("💰 Total Income", f"${total_income:,.2f}")
with col2:
    st.metric("💸 Total Expenses", f"${total_expenses:,.2f}")
with col3:
    delta_color = "normal" if net_balance >= 0 else "inverse"
    st.metric("💵 Net Balance", f"${net_balance:,.2f}", 
              delta=f"${abs(net_balance):,.2f}" if net_balance >= 0 else f"-${abs(net_balance):,.2f}")
with col4:
    st.metric("📊 Avg Daily Spend", f"${avg_daily_spending:,.2f}")
with col5:
    st.metric("🔢 Transactions", transaction_count)

# Second row of metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📈 Projected Monthly", f"${projected_monthly:,.2f}")
with col2:
    st.metric("🎯 Largest Expense", f"${largest_expense:,.2f}")
with col3:
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    st.metric("💎 Savings Rate", f"{savings_rate:.1f}%")
with col4:
    burn_rate = total_expenses / days_in_period if days_in_period > 0 else 0
    st.metric("🔥 Daily Burn Rate", f"${burn_rate:,.2f}")

st.divider()

# Enhanced Visualizations - TRENDS FOCUSED
st.header("� Spending Trends & Analysis")

# Prepare expenses data
expenses_df = filtered_df[filtered_df["Amount"] < 0].copy()
expenses_df["Amount"] = abs(expenses_df["Amount"])

# Row 1: Main trend lines
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Daily Spending Trend (All Cards)")
    if not expenses_df.empty:
        daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
        
        # Add 7-day moving average
        daily_spending['7-Day Avg'] = daily_spending['Amount'].rolling(window=7, min_periods=1).mean()
        
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(
            x=daily_spending['Date'], 
            y=daily_spending['Amount'],
            mode='lines+markers',
            name='Daily Spending',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=6)
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily_spending['Date'], 
            y=daily_spending['7-Day Avg'],
            mode='lines',
            name='7-Day Average',
            line=dict(color='#4ECDC4', width=3, dash='dash')
        ))
        fig_daily.update_layout(
            title="Daily Expenses with Moving Average",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("No expense data available")

with col2:
    st.subheader("📊 Category Trends Over Time")
    if not expenses_df.empty:
        category_daily = expenses_df.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
        
        fig_cat_trend = px.line(category_daily, 
                               x='Date', 
                               y='Amount',
                               color='Category',
                               title="Spending by Category Over Time",
                               markers=True)
        fig_cat_trend.update_layout(hovermode='x unified')
        st.plotly_chart(fig_cat_trend, use_container_width=True)
    else:
        st.info("No expense data available")

# Row 2: Monthly and Weekly patterns
col1, col2 = st.columns(2)

with col1:
    st.subheader("📆 Monthly Spending Comparison")
    if not filtered_df.empty:
        monthly_df = filtered_df.copy()
        monthly_df['Month'] = pd.to_datetime(monthly_df['Date']).dt.to_period('M').astype(str)
        
        monthly_income = monthly_df[monthly_df['Amount'] > 0].groupby('Month')['Amount'].sum().reset_index()
        monthly_income.columns = ['Month', 'Income']
        
        monthly_expenses = monthly_df[monthly_df['Amount'] < 0].groupby('Month')['Amount'].sum().reset_index()
        monthly_expenses['Amount'] = abs(monthly_expenses['Amount'])
        monthly_expenses.columns = ['Month', 'Expenses']
        
        monthly_combined = pd.merge(monthly_income, monthly_expenses, on='Month', how='outer').fillna(0)
        monthly_melted = monthly_combined.melt(id_vars='Month', var_name='Type', value_name='Amount')
        
        fig_monthly = px.bar(monthly_melted, 
                            x='Month', 
                            y='Amount', 
                            color='Type',
                            barmode='group',
                            title="Income vs Expenses by Month",
                            color_discrete_map={'Income': '#4ECDC4', 'Expenses': '#FF6B6B'})
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No data available")

with col2:
    st.subheader("📅 Day of Week Analysis")
    if not expenses_df.empty:
        expenses_df['DayOfWeek'] = expenses_df['Date'].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        day_spending = expenses_df.groupby('DayOfWeek')['Amount'].agg(['sum', 'mean', 'count']).reset_index()
        day_spending['DayOfWeek'] = pd.Categorical(day_spending['DayOfWeek'], categories=day_order, ordered=True)
        day_spending = day_spending.sort_values('DayOfWeek')
        
        fig_dow = go.Figure()
        fig_dow.add_trace(go.Bar(
            x=day_spending['DayOfWeek'],
            y=day_spending['mean'],
            name='Average',
            marker_color='#FF6B6B',
            text=day_spending['mean'].round(2),
            textposition='outside'
        ))
        fig_dow.update_layout(
            title="Average Spending by Day of Week",
            xaxis_title="Day",
            yaxis_title="Average Amount ($)"
        )
        st.plotly_chart(fig_dow, use_container_width=True)
    else:
        st.info("No expense data available")

# Row 3: Card-specific analysis if multiple cards
if 'Card' in filtered_df.columns and len(filtered_df['Card'].unique()) > 1:
    st.subheader("💳 Individual Card Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Spending Distribution by Card**")
        card_expenses = expenses_df.groupby('Card')['Amount'].sum().reset_index()
        card_expenses = card_expenses.sort_values('Amount', ascending=False)
        
        fig_card_pie = px.pie(card_expenses, 
                             names='Card', 
                             values='Amount',
                             title="Total Spending per Card",
                             hole=0.4)
        st.plotly_chart(fig_card_pie, use_container_width=True)
    
    with col2:
        st.markdown("**Card Usage Over Time**")
        card_daily = expenses_df.groupby(['Date', 'Card'])['Amount'].sum().reset_index()
        
        fig_card_trend = px.area(card_daily,
                                x='Date',
                                y='Amount',
                                color='Card',
                                title="Daily Spending by Card")
        st.plotly_chart(fig_card_trend, use_container_width=True)
    
    # Card comparison table
    st.markdown("**Card Comparison Summary**")
    card_summary = expenses_df.groupby('Card').agg({
        'Amount': ['sum', 'mean', 'count']
    }).round(2)
    card_summary.columns = ['Total Spent', 'Avg Transaction', 'Transaction Count']
    card_summary = card_summary.sort_values('Total Spent', ascending=False)
    st.dataframe(card_summary, use_container_width=True)

st.divider()

# Row 4: Category breakdown
st.subheader("🏷️ Category Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Expense Distribution**")
    if not expenses_df.empty:
        category_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index()
        category_totals = category_totals.sort_values("Amount", ascending=False)
        
        fig_pie = px.pie(category_totals, 
                        names="Category", 
                        values="Amount", 
                        title="Spending by Category",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense data available")

with col2:
    st.markdown("**Top Categories**")
    if not expenses_df.empty:
        category_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index()
        category_totals = category_totals.sort_values("Amount", ascending=True)
        
        fig_bar = px.bar(category_totals, 
                        x="Amount", 
                        y="Category", 
                        orientation='h',
                        title="Spending by Category",
                        color="Amount",
                        color_continuous_scale="Reds")
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No expense data available")

st.divider()

# Insights section
st.subheader("💡 Key Insights")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**🔝 Top 5 Expenses**")
    if not expenses_df.empty:
        top_expenses = expenses_df.nlargest(5, 'Amount')[['Date', 'Description', 'Amount']]
        top_expenses['Date'] = top_expenses['Date'].dt.strftime('%m/%d')
        for idx, row in top_expenses.iterrows():
            st.write(f"• {row['Description'][:25]}... - ${row['Amount']:.2f}")
    else:
        st.info("No expenses")

with col2:
    st.markdown("**📅 Spending Stats**")
    if not expenses_df.empty:
        days = (filtered_df['Date'].max() - filtered_df['Date'].min()).days + 1
        avg_daily = total_expenses / days if days > 0 else 0
        st.metric("Avg Daily", f"${avg_daily:.2f}")
        st.metric("Avg per Txn", f"${total_expenses/len(expenses_df):.2f}" if len(expenses_df) > 0 else "$0.00")
    else:
        st.info("No expenses")

with col3:
    st.markdown("**📊 Category Leaders**")
    if not expenses_df.empty:
        top_cat = expenses_df.groupby('Category')['Amount'].sum().idxmax()
        top_cat_amt = expenses_df.groupby('Category')['Amount'].sum().max()
        st.metric("Top Category", top_cat)
        st.metric("Amount", f"${top_cat_amt:.2f}")
    else:
        st.info("No data")

with col4:
    st.markdown("**🎯 Spending Pace**")
    if not expenses_df.empty and len(all_card_info) > 0:
        # Calculate spending rate for first card with due date
        card_with_due = next((c for c in all_card_info if c['due_date']), None)
        if card_with_due and card_with_due['due_date']:
            days_in_period = (card_with_due['due_date'] - pd.Timestamp.now()).days
            if days_in_period > 0:
                daily_rate = total_expenses / days_in_period
                st.metric("Daily Rate", f"${daily_rate:.2f}")
                projected = card_with_due['new_balance'] + (daily_rate * days_in_period)
                st.metric("Projected", f"${projected:.2f}")
            else:
                st.info("Statement period ended")
        else:
            st.info("No due date info")
    else:
        st.info("No data")

st.divider()

# Enhanced Visualizations with Tabs
st.header("📈 Spending Trends & Insights")

# Prepare data
expenses_df = filtered_df[filtered_df["Amount"] < 0].copy()
expenses_df["Amount"] = abs(expenses_df["Amount"])

if not expenses_df.empty:
    expenses_df['DayOfWeek'] = expenses_df['Date'].dt.day_name()
    expenses_df['WeekDay'] = expenses_df['Date'].dt.dayofweek
    expenses_df['Month'] = expenses_df['Date'].dt.to_period('M').astype(str)

# Create tabs for organized viewing
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📅 Time Patterns", "🏷️ Categories", "💳 Cards"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Daily Spending with Moving Averages**")
        if not expenses_df.empty:
            daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
            daily_spending['7-Day MA'] = daily_spending['Amount'].rolling(window=7, min_periods=1).mean()
            daily_spending['14-Day MA'] = daily_spending['Amount'].rolling(window=14, min_periods=1).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_spending['Date'], y=daily_spending['Amount'],
                                name='Daily', marker_color='rgba(255,107,107,0.6)'))
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['7-Day MA'],
                                    mode='lines', name='7-Day Avg', line=dict(color='#4ECDC4', width=3)))
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['14-Day MA'],
                                    mode='lines', name='14-Day Avg', line=dict(color='#A78BFA', width=2, dash='dash')))
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            if len(daily_spending) >= 7:
                recent_avg = daily_spending['Amount'].tail(7).mean()
                overall_avg = daily_spending['Amount'].mean()
                trend_pct = ((recent_avg - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
                
                if abs(trend_pct) > 10:
                    if trend_pct > 0:
                        st.warning(f"⚠️ Spending up {trend_pct:.1f}% in last 7 days")
                    else:
                        st.success(f"✅ Spending down {abs(trend_pct):.1f}% in last 7 days")
        else:
            st.info("No expense data")
    
    with col2:
        st.markdown("**Cumulative Spending**")
        if not expenses_df.empty:
            daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
            daily_spending['Cumulative'] = daily_spending['Amount'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['Cumulative'],
                                    mode='lines', fill='tozeroy', name='Cumulative',
                                    line=dict(color='#FF6B6B', width=3),
                                    fillcolor='rgba(255,107,107,0.2)'))
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            if len(daily_spending) > 1:
                days_elapsed = (daily_spending['Date'].max() - daily_spending['Date'].min()).days + 1
                total_spent = daily_spending['Cumulative'].iloc[-1]
                daily_velocity = total_spent / days_elapsed if days_elapsed > 0 else 0
                st.info(f"💨 ${daily_velocity:.2f}/day → ${daily_velocity * 30:.2f}/month projected")
        else:
            st.info("No expense data")
    
    st.markdown("**Category Trends Over Time**")
    if not expenses_df.empty:
        category_daily = expenses_df.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
        fig = px.area(category_daily, x='Date', y='Amount', color='Category', height=350)
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Day of Week Analysis**")
        if not expenses_df.empty:
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_spending = expenses_df.groupby('DayOfWeek')['Amount'].agg(['mean', 'count']).reset_index()
            day_spending['DayOfWeek'] = pd.Categorical(day_spending['DayOfWeek'], categories=day_order, ordered=True)
            day_spending = day_spending.sort_values('DayOfWeek')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=day_spending['DayOfWeek'], y=day_spending['mean'],
                                marker_color='#FF6B6B', text=day_spending['mean'].round(2),
                                textposition='outside'))
            fig.update_layout(height=350, yaxis_title="Avg Amount ($)")
            st.plotly_chart(fig, use_container_width=True)
            
            max_day = day_spending.loc[day_spending['mean'].idxmax(), 'DayOfWeek']
            min_day = day_spending.loc[day_spending['mean'].idxmin(), 'DayOfWeek']
            st.info(f"Most: **{max_day}** | Least: **{min_day}**")
        else:
            st.info("No expense data")
    
    with col2:
        st.markdown("**Weekday vs Weekend**")
        if not expenses_df.empty:
            expenses_df['DayType'] = expenses_df['WeekDay'].apply(lambda x: 'Weekend' if x >= 5 else 'Weekday')
            daytype_spending = expenses_df.groupby('DayType')['Amount'].agg(['sum', 'mean']).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Total', x=daytype_spending['DayType'], y=daytype_spending['sum'],
                                marker_color='#4ECDC4'))
            fig.add_trace(go.Bar(name='Average', x=daytype_spending['DayType'], y=daytype_spending['mean'],
                                marker_color='#FF6B6B'))
            fig.update_layout(barmode='group', height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data")
    
    st.markdown("**Spending Heatmap**")
    if not expenses_df.empty and len(expenses_df) > 7:
        expenses_df['WeekNum'] = expenses_df['Date'].dt.isocalendar().week
        heatmap_data = expenses_df.groupby(['WeekNum', 'DayOfWeek'])['Amount'].sum().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='WeekNum', columns='DayOfWeek', values='Amount').fillna(0)
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(columns=[d for d in day_order if d in heatmap_pivot.columns])
        
        fig = go.Figure(data=go.Heatmap(z=heatmap_pivot.values, x=heatmap_pivot.columns,
                                        y=[f"Week {w}" for w in heatmap_pivot.index],
                                        colorscale='Reds'))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Category Distribution**")
        if not expenses_df.empty:
            category_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index()
            category_totals = category_totals.sort_values("Amount", ascending=False)
            
            fig = px.pie(category_totals, names="Category", values="Amount", hole=0.4, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data")
    
    with col2:
        st.markdown("**Top 10 Merchants**")
        if not expenses_df.empty:
            top_merchants = expenses_df.groupby("Description")["Amount"].sum().nlargest(10).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(y=top_merchants['Description'], x=top_merchants['Amount'],
                                orientation='h', marker_color='#4ECDC4'))
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data")
    
    st.markdown("**Category Breakdown Table**")
    if not expenses_df.empty:
        cat_summary = expenses_df.groupby("Category").agg({
            'Amount': ['sum', 'mean', 'count']
        }).round(2)
        cat_summary.columns = ['Total', 'Average', 'Count']
        cat_summary = cat_summary.sort_values('Total', ascending=False)
        st.dataframe(cat_summary, use_container_width=True)

with tab4:
    if 'Card' in filtered_df.columns and len(filtered_df['Card'].unique()) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Spending by Card**")
            card_expenses = expenses_df.groupby('Card')['Amount'].sum().reset_index()
            card_expenses = card_expenses.sort_values('Amount', ascending=False)
            
            fig = px.pie(card_expenses, names='Card', values='Amount', hole=0.4, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Card Usage Over Time**")
            card_daily = expenses_df.groupby(['Date', 'Card'])['Amount'].sum().reset_index()
            
            fig = px.area(card_daily, x='Date', y='Amount', color='Card', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("**Card Comparison**")
        card_summary = expenses_df.groupby('Card').agg({
            'Amount': ['sum', 'mean', 'count']
        }).round(2)
        card_summary.columns = ['Total Spent', 'Avg Transaction', 'Transaction Count']
        card_summary = card_summary.sort_values('Total Spent', ascending=False)
        st.dataframe(card_summary, use_container_width=True)
    else:
        st.info("Upload multiple card statements to see card comparison")

st.divider()

# Budget Tracking Section (moved to bottom)
st.header("💰 Budget Management")

# Budget goals in sidebar
st.sidebar.header("💵 Budget Goals")
st.sidebar.markdown("*Set monthly budget limits per category*")

budget_goals = {}
for cat in sorted(df["Category"].unique()):
    default_val = 500.0 if cat not in ["Income/Payments"] else 0.0
    budget_goals[cat] = st.sidebar.number_input(
        f"{cat}",
        min_value=0.0,
        value=default_val,
        step=50.0,
        key=f"budget_{cat}"
    )

# Budget tracking display
for cat in sorted(filtered_df["Category"].unique()):
    if cat == "Income/Payments":
        continue
        
    cat_data = filtered_df[filtered_df["Category"] == cat]
    spent = abs(cat_data[cat_data["Amount"] < 0]["Amount"].sum())
    limit = budget_goals.get(cat, 0)
    
    if limit > 0:
        progress = min(spent / limit, 1.0)
        remaining = limit - spent
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{cat}**: ${spent:.2f} / ${limit:.2f}")
            st.progress(progress)
        with col2:
            if spent > limit:
                st.error(f"⚠️ Over by ${abs(remaining):.2f}")
            else:
                st.success(f"✓ ${remaining:.2f} left")

# Budget performance summary
st.subheader("📊 Budget Performance")
col1, col2, col3 = st.columns(3)

with col1:
    total_budget = sum(v for k, v in budget_goals.items() if k != "Income/Payments" and v > 0)
    if total_budget > 0:
        budget_used_pct = (total_expenses / total_budget * 100)
        st.metric("Total Budget", f"${total_budget:,.2f}")
        st.metric("Budget Used", f"{budget_used_pct:.1f}%")
    else:
        st.info("Set budget goals in sidebar →")

with col2:
    if total_budget > 0:
        if budget_used_pct > 100:
            st.error(f"⚠️ Over budget by ${total_expenses - total_budget:.2f}")
        else:
            st.success(f"✅ Under budget by ${total_budget - total_expenses:.2f}")
        
        remaining_budget = total_budget - total_expenses
        days_left = (pd.to_datetime(end_date) - pd.Timestamp.now()).days
        if days_left > 0 and remaining_budget > 0:
            daily_allowance = remaining_budget / days_left
            st.metric("Daily Allowance", f"${daily_allowance:.2f}")

with col3:
    if budget_goals:
        over_budget_cats = [cat for cat in filtered_df["Category"].unique() 
                           if budget_goals.get(cat, 0) > 0 and 
                           abs(filtered_df[filtered_df["Category"] == cat]["Amount"].sum()) > budget_goals.get(cat, 0)]
        
        if over_budget_cats:
            st.error(f"⚠️ {len(over_budget_cats)} categor{'y' if len(over_budget_cats)==1 else 'ies'} over budget")
            for cat in over_budget_cats:
                st.write(f"• {cat}")
        else:
            st.success("✅ All categories within budget!")

st.divider()

# Transactions Table
st.header("📋 Transaction Details")

# Add search and additional filters
col1, col2, col3 = st.columns(3)

with col1:
    search_term = st.text_input("🔍 Search transactions", "")

with col2:
    transaction_type = st.selectbox("Transaction Type", ["All", "Expenses", "Income"])

with col3:
    sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High to Low)", "Amount (Low to High)"])

# Apply search and filters
display_df = filtered_df.copy()

if search_term:
    display_df = display_df[display_df['Description'].str.contains(search_term, case=False, na=False)]

if transaction_type == "Expenses":
    display_df = display_df[display_df['Amount'] < 0]
elif transaction_type == "Income":
    display_df = display_df[display_df['Amount'] > 0]

# Apply sorting
if sort_by == "Date (Newest)":
    display_df = display_df.sort_values('Date', ascending=False)
elif sort_by == "Date (Oldest)":
    display_df = display_df.sort_values('Date', ascending=True)
elif sort_by == "Amount (High to Low)":
    display_df = display_df.sort_values('Amount', ascending=False)
elif sort_by == "Amount (Low to High)":
    display_df = display_df.sort_values('Amount', ascending=True)

# Format the display
display_df_formatted = display_df.copy()
display_df_formatted['Date'] = display_df_formatted['Date'].dt.strftime('%Y-%m-%d')
display_df_formatted['Amount'] = display_df_formatted['Amount'].apply(lambda x: f"${x:,.2f}")

st.dataframe(display_df_formatted, use_container_width=True, hide_index=True)

# Export option
st.download_button(
    label="📥 Download Transactions as CSV",
    data=display_df.to_csv(index=False).encode('utf-8'),
    file_name=f"transactions_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
