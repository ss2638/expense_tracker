
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
    pending_sync_transaction = None  # Track last Synchrony transaction for multi-line descriptions
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
                    # Note: Don't stop at "Daily Cash" alone - it appears in Apple Card transaction columns
                    if "2025 Totals Year-to-Date" in line or "INTEREST CHARGES" in line or "Apple Card Monthly Installments" in line or "Total Daily Cash this month" in line:
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
                        # Followed by product details on next line(s): "-, - COLLATED 23G, 18G BRADS..."
                        # Date Reference# Description Amount
                        match_sync = re.match(r'^(\d{1,2}/\d{1,2})\s+(\d+\s+)?(.+?)\s+(\-?\$[\d,]+\.\d{2})\s*$', line.strip())
                        
                        # Synchrony product detail line (starts with "-, -" or similar, or just product text without date/amount)
                        # Check if line has no date pattern and no dollar amount (likely a continuation)
                        is_potential_detail = not re.match(r'^\d{1,2}/\d{1,2}', line.strip()) and not re.search(r'\$[\d,]+\.\d{2}', line.strip())
                        match_sync_detail = is_potential_detail and pending_sync_transaction is not None and len(line.strip()) > 3
                        
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
                        # Example: "10/05/2025 APPLE.COM/BILL ONE APPLE PARK WAY 866-712-7753 96014 CA USA 3% $1.35 $44.99"
                        match_apple = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d+%)\s+\$?([\d.]+)\s+([-]?\$?[\d,]+\.\d{2})$', line.strip())
                        
                        # Apple Card payment format: MM/DD/YYYY Description -$Amount or $Amount
                        match_apple_payment = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})$', line.strip())
                        
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
                                    # Clean up description - keep meaningful parts
                                    description = re.sub(r'STORE\s+\d+\s+', '', description)  # Remove "STORE 0678 "
                                    description = re.sub(r'\s+[A-Z]{2}$', '', description)  # Remove state codes at end
                                    
                                    # Store this transaction temporarily to potentially add product details
                                    pending_sync_transaction = [date, description.strip(), amount]
                                    transactions.append(pending_sync_transaction)
                            except Exception as e:
                                pending_sync_transaction = None
                                continue
                        
                        elif match_sync_detail:
                            # This is a product detail line for the previous Synchrony transaction
                            # Append to the description of the last transaction
                            detail = line.strip()
                            # Remove common prefixes like "-, -" or "-,-"
                            detail = re.sub(r'^[-,\s]+', '', detail)
                            if detail and len(detail) > 3:  # Only add meaningful details
                                # Update the description in the last added transaction
                                pending_sync_transaction[1] += " - " + detail
                            continue
                        
                        elif not match_sync_detail and pending_sync_transaction:
                            # No longer in detail lines, clear pending transaction
                            pending_sync_transaction = None
                        
                        elif match_dcu:
                            pending_sync_transaction = None  # Clear pending Synchrony transaction
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
                            pending_sync_transaction = None  # Clear pending Synchrony transaction
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
                            daily_cash_percent = match_apple.group(3)  # e.g., "3%"
                            daily_cash_amount = match_apple.group(4)   # e.g., "1.35"
                            amount_str = match_apple.group(5).replace('$', '').replace(',', '')
                            
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
                                amount = float(amount_str)
                                # Make payments positive if they're showing as negative
                                if amount < 0:
                                    amount = abs(amount)
                                
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
    description_lower = description.lower()
    
    # ========== PRIORITY 1: Income & Payments (CHECK FIRST) ==========
    payment_keywords = [
        "payment thank you", "online payment", "autopay", "automatic payment",
        "payment received", "payment - thank you", "mobile payment",
        "internet payment", "ach deposit", "internet transfer",
        "payroll", "salary", "direct deposit",
        "statement credit", "adjustment credit", "fee reversal", 
        "interest refund", "balance transfer", "electronic payment"
    ]
    # Exclude: Regular PayPal purchases should not be treated as payments
    if any(keyword in description_lower for keyword in payment_keywords):
        # But check if it's a PayPal purchase (not a payment)
        if "paypal" in description_lower and any(merchant in description_lower for merchant in ["walmart", "adobe", "ebay"]):
            pass  # Continue to regular categorization
        else:
            return "Income/Payments"
    
    # ========== PRIORITY 2: Groceries & Food ==========
    # Grocery Stores
    grocery_stores = [
        "walmart", "wm supercenter", "wal-mart", "target", "costco", "sam's club",
        "kroger", "publix", "whole foods", "trader joe", "safeway", "albertsons",
        "aldi", "lidl", "food lion", "giant", "stop & shop", "wegmans",
        "indifresh", "suvidha", "patel brothers", "indian grocery"
    ]
    if any(store in description_lower for store in grocery_stores):
        return "Groceries"
    
    # Restaurants & Dining
    restaurants = [
        "restaurant", "cafe", "coffee", "starbucks", "dunkin", "mcdonald",
        "burger", "pizza", "domino", "papa john", "chipotle", "taco bell",
        "subway", "panera", "chick-fil-a", "wendy", "kfc", "arby",
        "zaxby", "desi street", "biryani", "chutney", "flippin pizza",
        "steakhouse", "grill", "bakery", "bar", "pub", "tap room",
        "applebee", "chili", "olive garden", "red lobster", "outback",
        "kilwins", "confections", "indi fresh", "jerusalem bakery",
        "barleygarden", "brew deck", "craft burger"
    ]
    if any(restaurant in description_lower for restaurant in restaurants):
        return "Food & Dining"
    
    # ========== PRIORITY 3: Bills & Utilities ==========
    utilities = [
        "utility", "electric", "power", "water", "gas", "natgas", "sawnee",
        "georgia power", "at&t", "verizon", "t-mobile", "comcast", "xfinity",
        "internet", "cable", "phone", "wireless", "apple.com/bill",
        "sanitation", "waste", "trash", "garbage", "sewage"
    ]
    if any(util in description_lower for util in utilities):
        return "Bills & Utilities"
    
    # ========== PRIORITY 4: Transportation ==========
    transportation = [
        "gas", "fuel", "shell", "exxon", "chevron", "bp", "mobil",
        "uber", "lyft", "taxi", "parking", "transit", "toll",
        "costco gas", "gas station", "natgas"
    ]
    if any(trans in description_lower for trans in transportation):
        # Exception: Natural gas is a utility, not transportation
        if "natgas" in description_lower or "georgia natural" in description_lower:
            return "Bills & Utilities"
        return "Transportation"
    
    # ========== PRIORITY 5: Healthcare ==========
    healthcare = [
        "pharmacy", "cvs", "walgreens", "rite aid", "doctor", "hospital",
        "medical", "dental", "vision", "lab", "laboratory", "clinic",
        "health", "medicine", "prescription", "inspire ob"
    ]
    if any(health in description_lower for health in healthcare):
        return "Healthcare"
    
    # ========== PRIORITY 6: Home Improvement ==========
    home_improvement = [
        "home depot", "lowe", "lowes", "ace hardware", "true value",
        "menards", "harbor freight", "lumber", "hardware",
        "furring", "veneer", "valspar", "paint", "roller", "jigsaw"
    ]
    if any(store in description_lower for store in home_improvement):
        return "Home Improvement"
    
    # ========== PRIORITY 7: Shopping (Retail & Online) ==========
    # Online marketplaces
    if "amazon" in description_lower or "amzn" in description_lower or "ebay" in description_lower:
        return "Shopping"
    
    # Retail stores
    retail_stores = [
        "macy", "kohl", "jcpenney", "nordstrom", "dillard", "sears",
        "ross", "tj maxx", "marshalls", "burlington", "target.com",
        "h&m", "zara", "gap", "old navy", "banana republic",
        "dollar tree", "dollar general", "five below", "big lots",
        "hobby lobby", "michaels", "joann", "craft",
        "best buy", "apple store", "microsoft store",
        "rack room shoes", "foot locker", "nike", "adidas"
    ]
    if any(store in description_lower for store in retail_stores):
        return "Shopping"
    
    # ========== PRIORITY 8: Subscriptions ==========
    subscriptions = [
        "netflix", "hulu", "disney", "prime video", "hbo", "paramount",
        "spotify", "apple music", "youtube", "youtube premium",
        "adobe", "microsoft 365", "office 365", "dropbox", "icloud",
        "github", "playstation", "xbox", "nintendo", "steam",
        "gym", "fitness", "active n fit"
    ]
    if any(sub in description_lower for sub in subscriptions):
        return "Subscriptions"
    
    # ========== PRIORITY 9: Entertainment ==========
    entertainment = [
        "movie", "theater", "cinema", "amc", "regal", "cinemark",
        "concert", "ticket", "event", "sports", "game"
    ]
    if any(ent in description_lower for ent in entertainment):
        return "Entertainment"
    
    # ========== PRIORITY 10: Professional Services ==========
    services = [
        "haircut", "salon", "barber", "spa", "massage",
        "lawyer", "attorney", "accountant", "consultant",
        "ahs.com", "warranty", "protection plan"
    ]
    if any(service in description_lower for service in services):
        return "Professional Services"
    
    # ========== PRIORITY 11: Finance & Banking ==========
    finance = [
        "bank fee", "atm", "wire transfer", "money order",
        "interest charged", "late fee", "annual fee",
        "electronic payment", "ba electronic"
    ]
    if any(fin in description_lower for fin in finance):
        return "Finance & Banking"
    
    # ========== DEFAULT: Other ==========
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
        
        # Fix amount signs: Payments/Credits should be positive (they reduce what you owe)
        # Expenses should be negative (they increase what you owe)
        # If a payment is currently negative, flip it to positive
        df.loc[df["Category"] == "Income/Payments", "Amount"] = df.loc[df["Category"] == "Income/Payments", "Amount"].abs()
        
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
        df.loc[df["Category"] == "Income/Payments", "Amount"] = df.loc[df["Category"] == "Income/Payments", "Amount"].abs()
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
    df.loc[df["Category"] == "Income/Payments", "Amount"] = df.loc[df["Category"] == "Income/Payments", "Amount"].abs()
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

# Filter out payment/credit transactions for accurate metrics
non_payment_df = filtered_df[filtered_df["Category"] != "Income/Payments"].copy()
payment_count = len(filtered_df) - len(non_payment_df)

# Show info if payments were filtered
if payment_count > 0:
    st.info(f"ℹ️ **{payment_count} payment/credit transactions** filtered out from metrics and charts (Card payments, refunds, credits, etc.)")

# Calculate metrics (excluding payments)
total_income = non_payment_df[non_payment_df["Amount"] > 0]["Amount"].sum()
total_expenses = abs(non_payment_df[non_payment_df["Amount"] < 0]["Amount"].sum())
net_balance = total_income - total_expenses
transaction_count = len(non_payment_df)

# Calculate additional insights
expenses_df_temp = non_payment_df[non_payment_df["Amount"] < 0].copy()
if not expenses_df_temp.empty:
    avg_daily_spending = abs(expenses_df_temp.groupby("Date")["Amount"].sum().mean())
    largest_expense = abs(expenses_df_temp["Amount"].min())
    days_in_period = (non_payment_df["Date"].max() - non_payment_df["Date"].min()).days + 1
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

# Prepare expenses data (exclude payment transactions)
expenses_df = filtered_df[(filtered_df["Amount"] < 0) & (filtered_df["Category"] != "Income/Payments")].copy()
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

# Prepare data (exclude payment transactions)
expenses_df = filtered_df[(filtered_df["Amount"] < 0) & (filtered_df["Category"] != "Income/Payments")].copy()
expenses_df["Amount"] = abs(expenses_df["Amount"])

if not expenses_df.empty:
    expenses_df['DayOfWeek'] = expenses_df['Date'].dt.day_name()
    expenses_df['WeekDay'] = expenses_df['Date'].dt.dayofweek
    expenses_df['Month'] = expenses_df['Date'].dt.to_period('M').astype(str)

# Create tabs for organized viewing
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Overview", "📅 Time Patterns", "🏷️ Categories", "💳 Cards", "🎯 Goals & Forecasts", "💰 Merchant Insights"])

with tab1:
    # Row 1: Main trends with enhancements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Daily Spending with Anomaly Detection**")
        if not expenses_df.empty:
            daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
            daily_spending['7-Day MA'] = daily_spending['Amount'].rolling(window=7, min_periods=1).mean()
            daily_spending['14-Day MA'] = daily_spending['Amount'].rolling(window=14, min_periods=1).mean()
            
            # Calculate volatility bands (Bollinger-style)
            daily_spending['Std'] = daily_spending['Amount'].rolling(window=7, min_periods=1).std()
            daily_spending['Upper Band'] = daily_spending['7-Day MA'] + (2 * daily_spending['Std'])
            daily_spending['Lower Band'] = daily_spending['7-Day MA'] - (2 * daily_spending['Std'])
            
            # Detect anomalies (spending > upper band)
            daily_spending['Anomaly'] = daily_spending['Amount'] > daily_spending['Upper Band']
            
            fig = go.Figure()
            
            # Normal spending (bars)
            normal_days = daily_spending[~daily_spending['Anomaly']]
            fig.add_trace(go.Bar(x=normal_days['Date'], y=normal_days['Amount'],
                                name='Daily', marker_color='rgba(255,107,107,0.6)'))
            
            # Anomalies (highlighted bars)
            anomaly_days = daily_spending[daily_spending['Anomaly']]
            if not anomaly_days.empty:
                fig.add_trace(go.Bar(x=anomaly_days['Date'], y=anomaly_days['Amount'],
                                    name='⚠️ Spike', marker_color='rgba(239,68,68,0.9)'))
            
            # Moving averages
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['7-Day MA'],
                                    mode='lines', name='7-Day Avg', line=dict(color='#4ECDC4', width=3)))
            
            # Volatility bands (shaded area)
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['Upper Band'],
                                    mode='lines', name='Upper Band', line=dict(width=0),
                                    showlegend=False))
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['Lower Band'],
                                    mode='lines', name='Lower Band', line=dict(width=0),
                                    fill='tonexty', fillcolor='rgba(78,205,196,0.1)',
                                    showlegend=True))
            
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            # Smart alerts
            if not anomaly_days.empty:
                st.warning(f"🚨 {len(anomaly_days)} anomaly spike(s) detected!")
                for _, row in anomaly_days.head(3).iterrows():
                    st.write(f"• {row['Date'].strftime('%b %d')}: ${row['Amount']:.2f} (${row['Amount'] - row['7-Day MA']:.2f} above avg)")
            
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
        st.markdown("**⚡ Spending Pace Gauge**")
        if not expenses_df.empty:
            days_elapsed = (filtered_df['Date'].max() - filtered_df['Date'].min()).days + 1
            days_in_month = 30
            
            total_spent = expenses_df['Amount'].sum()
            expected_by_now = (total_spent / days_elapsed) * min(days_elapsed, days_in_month)
            
            # Gauge chart
            pace_pct = (total_spent / expected_by_now * 100) if expected_by_now > 0 else 100
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=total_spent,
                delta={'reference': expected_by_now, 'valueformat': '$,.0f'},
                title={'text': f"Spending vs Expected<br><sub>Day {days_elapsed} of {days_in_month}</sub>"},
                gauge={
                    'axis': {'range': [None, expected_by_now * 1.5]},
                    'bar': {'color': '#FF6B6B'},
                    'steps': [
                        {'range': [0, expected_by_now * 0.8], 'color': '#D1FAE5'},
                        {'range': [expected_by_now * 0.8, expected_by_now * 1.2], 'color': '#FEF3C7'},
                        {'range': [expected_by_now * 1.2, expected_by_now * 1.5], 'color': '#FEE2E2'}
                    ],
                    'threshold': {
                        'line': {'color': '#3B82F6', 'width': 4},
                        'thickness': 0.75,
                        'value': expected_by_now
                    }
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Pace insights
            if pace_pct > 120:
                st.error(f"🔥 Spending {pace_pct-100:.0f}% faster than expected!")
            elif pace_pct < 80:
                st.success(f"💚 Spending {100-pace_pct:.0f}% slower than expected!")
            else:
                st.info(f"📊 On pace (±20% of expected)")
        else:
            st.info("No expense data")
    
    # Row 2: Enhanced cumulative + category breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Cumulative Spending with Budget Goal**")
        if not expenses_df.empty:
            daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
            daily_spending['Cumulative'] = daily_spending['Amount'].cumsum()
            
            # Calculate projected end-of-period
            days_elapsed = (daily_spending['Date'].max() - daily_spending['Date'].min()).days + 1
            total_spent = daily_spending['Cumulative'].iloc[-1]
            daily_rate = total_spent / days_elapsed if days_elapsed > 0 else 0
            projected_total = daily_rate * 30
            
            fig = go.Figure()
            
            # Actual cumulative
            fig.add_trace(go.Scatter(x=daily_spending['Date'], y=daily_spending['Cumulative'],
                                    mode='lines', fill='tozeroy', name='Actual Spending',
                                    line=dict(color='#FF6B6B', width=3),
                                    fillcolor='rgba(255,107,107,0.2)'))
            
            # Projected line
            if days_elapsed < 30:
                future_date = daily_spending['Date'].max() + pd.Timedelta(days=30-days_elapsed)
                fig.add_trace(go.Scatter(x=[daily_spending['Date'].max(), future_date],
                                        y=[total_spent, projected_total],
                                        mode='lines', name='Projected',
                                        line=dict(color='#A78BFA', width=2, dash='dash')))
            
            # Budget goal line (if available from sidebar)
            if 'budget_goals' in locals():
                total_budget = sum(v for k, v in budget_goals.items() if k != "Income/Payments" and v > 0)
                if total_budget > 0:
                    fig.add_trace(go.Scatter(x=[daily_spending['Date'].min(), daily_spending['Date'].max()],
                                            y=[total_budget, total_budget],
                                            mode='lines', name='Budget Goal',
                                            line=dict(color='#10B981', width=2, dash='dot')))
            
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"💨 **Daily Rate:** ${daily_rate:.2f}/day → **Projected:** ${projected_total:.2f}/month")
        else:
            st.info("No expense data")
    
    with col2:
        st.markdown("**🎯 Category Momentum (% Change)**")
        if not expenses_df.empty and len(expenses_df) > 14:
            # Calculate first half vs second half spending
            mid_date = expenses_df['Date'].min() + (expenses_df['Date'].max() - expenses_df['Date'].min()) / 2
            
            first_half = expenses_df[expenses_df['Date'] <= mid_date].groupby('Category')['Amount'].sum()
            second_half = expenses_df[expenses_df['Date'] > mid_date].groupby('Category')['Amount'].sum()
            
            # Calculate % change
            momentum = pd.DataFrame({
                'First Half': first_half,
                'Second Half': second_half
            }).fillna(0)
            
            momentum['Change %'] = ((momentum['Second Half'] - momentum['First Half']) / momentum['First Half'] * 100).fillna(0)
            momentum = momentum.sort_values('Change %', ascending=False)
            
            # Create diverging bar chart
            fig = go.Figure()
            
            colors = ['#EF4444' if x > 20 else '#F59E0B' if x > 0 else '#10B981' for x in momentum['Change %']]
            
            fig.add_trace(go.Bar(
                y=momentum.index,
                x=momentum['Change %'],
                orientation='h',
                marker_color=colors,
                text=[f"{x:+.0f}%" for x in momentum['Change %']],
                textposition='outside'
            ))
            
            fig.update_layout(
                height=400,
                xaxis_title="Change (%)",
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Top movers
            growing = momentum[momentum['Change %'] > 20].index.tolist()
            if growing:
                st.warning(f"📈 Growing: {', '.join(growing[:3])}")
        else:
            st.info("Need at least 14 days of data")
    
    # Full-width: Category trends area chart
    st.markdown("**🏷️ Category Spending Trends Over Time**")
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

with tab5:
    st.subheader("🎯 Goals, Forecasts & Financial Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💵 Budget Performance Overview**")
        if not expenses_df.empty and 'budget_goals' in locals():
            # Calculate budget metrics
            budget_data = []
            for cat in expenses_df['Category'].unique():
                spent = expenses_df[expenses_df['Category'] == cat]['Amount'].sum()
                limit = budget_goals.get(cat, 0)
                if limit > 0:
                    budget_data.append({
                        'Category': cat,
                        'Spent': spent,
                        'Budget': limit,
                        'Remaining': limit - spent,
                        'Usage %': (spent / limit * 100)
                    })
            
            if budget_data:
                budget_df = pd.DataFrame(budget_data).sort_values('Usage %', ascending=False)
                
                # Waterfall chart showing budget variance
                fig = go.Figure(go.Waterfall(
                    x=budget_df['Category'],
                    y=budget_df['Remaining'],
                    text=[f"${x:.0f}" for x in budget_df['Remaining']],
                    textposition="outside",
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    decreasing={"marker": {"color": "#EF4444"}},
                    increasing={"marker": {"color": "#10B981"}},
                ))
                fig.update_layout(
                    title="Budget Variance by Category",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Budget health score
                over_budget = len(budget_df[budget_df['Usage %'] > 100])
                total_cats = len(budget_df)
                health_score = max(0, 100 - (over_budget / total_cats * 100)) if total_cats > 0 else 100
                
                if health_score >= 80:
                    st.success(f"💚 Budget Health: {health_score:.0f}/100 - Excellent!")
                elif health_score >= 60:
                    st.info(f"📊 Budget Health: {health_score:.0f}/100 - Good")
                else:
                    st.error(f"⚠️ Budget Health: {health_score:.0f}/100 - Needs Attention")
            else:
                st.info("Set budget goals in sidebar to see analysis")
        else:
            st.info("Set budget goals in sidebar")
    
    with col2:
        st.markdown("**📈 Spending Forecast (Next 7 Days)**")
        if not expenses_df.empty and len(expenses_df) >= 7:
            # Simple forecast based on recent trend
            daily_spending = expenses_df.groupby("Date")["Amount"].sum().reset_index()
            recent_avg = daily_spending['Amount'].tail(7).mean()
            
            # Generate forecast dates
            last_date = daily_spending['Date'].max()
            forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
            forecast_amounts = [recent_avg] * 7
            
            # Add some variance
            import random
            random.seed(42)
            forecast_amounts_varied = [amt * (1 + random.uniform(-0.2, 0.2)) for amt in forecast_amounts]
            
            fig = go.Figure()
            
            # Historical
            fig.add_trace(go.Scatter(
                x=daily_spending['Date'].tail(14),
                y=daily_spending['Amount'].tail(14),
                mode='lines+markers',
                name='Historical',
                line=dict(color='#FF6B6B', width=2)
            ))
            
            # Forecast
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_amounts_varied,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#A78BFA', width=2, dash='dash')
            ))
            
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            projected_week = sum(forecast_amounts_varied)
            st.info(f"📊 Projected next 7 days: ${projected_week:.2f}")
        else:
            st.info("Need at least 7 days of data")
    
    # Full width: Financial Health Dashboard
    st.markdown("**💎 Financial Health Snapshot**")
    if not expenses_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Savings rate
            income_df = filtered_df[filtered_df['Amount'] > 0]
            total_income = income_df['Amount'].sum()
            total_expenses = expenses_df['Amount'].sum()
            savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=savings_rate,
                title={'text': "Savings Rate"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#10B981'},
                    'steps': [
                        {'range': [0, 20], 'color': '#FEE2E2'},
                        {'range': [20, 50], 'color': '#FEF3C7'},
                        {'range': [50, 100], 'color': '#D1FAE5'}
                    ]
                },
                number={'suffix': "%"}
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Spending efficiency (vs budget)
            if 'budget_goals' in locals():
                total_budget = sum(v for k, v in budget_goals.items() if k != "Income/Payments" and v > 0)
                efficiency = (total_budget - total_expenses) / total_budget * 100 if total_budget > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=max(0, efficiency),
                    title={'text': "Budget Efficiency"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': '#3B82F6'},
                        'steps': [
                            {'range': [0, 20], 'color': '#FEE2E2'},
                            {'range': [20, 50], 'color': '#FEF3C7'},
                            {'range': [50, 100], 'color': '#D1FAE5'}
                        ]
                    },
                    number={'suffix': "%"}
                ))
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Set budgets")
        
        with col3:
            # Category diversity (how spread out spending is)
            cat_spending = expenses_df.groupby('Category')['Amount'].sum()
            diversity = len(cat_spending) / 15 * 100  # 15 = total categories
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=diversity,
                title={'text': "Spending Diversity"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#F59E0B'},
                },
                number={'suffix': "%"}
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # Transaction frequency score
            days_active = expenses_df['Date'].nunique()
            total_days = (expenses_df['Date'].max() - expenses_df['Date'].min()).days + 1
            frequency_score = days_active / total_days * 100 if total_days > 0 else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=frequency_score,
                title={'text': "Activity Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#8B5CF6'},
                },
                number={'suffix': "%"}
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("💰 Merchant Insights & Spending Patterns")
    
    if not expenses_df.empty:
        # Filter out payments/credits/refunds from merchant analysis
        merchant_df = expenses_df[~expenses_df['Category'].isin(['Income/Payments'])].copy()
        
        # Also filter out common payment keywords in description
        payment_keywords = ['payment thank you', 'online payment', 'autopay', 'credit', 'refund', 
                           'cashback', 'rewards', 'adjustment', 'fee reversal']
        for keyword in payment_keywords:
            merchant_df = merchant_df[~merchant_df['Description'].str.lower().str.contains(keyword, na=False)]
        
        if merchant_df.empty:
            st.info("No merchant data available after filtering payments/credits")
        else:
            # Calculate merchant metrics
            merchant_totals = merchant_df.groupby("Description")["Amount"].agg(['sum', 'count', 'mean']).reset_index()
            merchant_totals.columns = ['Merchant', 'Total', 'Visits', 'Avg']
            merchant_totals['Loyalty Score'] = merchant_totals['Visits'] * merchant_totals['Total'] / 100
            merchant_totals = merchant_totals.sort_values('Total', ascending=False)
        
        # Top section: Key insights cards
        st.markdown("### 📊 Key Merchant Insights")
        
        # Add custom CSS for smaller font in merchant metrics
        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 1rem !important;
            line-height: 1.3 !important;
        }
        div[data-testid="stMetric"] label {
            font-size: 0.9rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            top_merchant = merchant_totals.iloc[0]
            st.metric(
                "🏆 Top Merchant",
                top_merchant['Merchant'][:30] + "..." if len(top_merchant['Merchant']) > 30 else top_merchant['Merchant'],
                f"${top_merchant['Total']:.0f}"
            )
        
        with col2:
            most_frequent = merchant_totals.sort_values('Visits', ascending=False).iloc[0]
            st.metric(
                "🔄 Most Frequent",
                most_frequent['Merchant'][:30] + "..." if len(most_frequent['Merchant']) > 30 else most_frequent['Merchant'],
                f"{int(most_frequent['Visits'])} visits"
            )
        
        with col3:
            highest_avg = merchant_totals.sort_values('Avg', ascending=False).iloc[0]
            st.metric(
                "💎 Highest Avg",
                highest_avg['Merchant'][:30] + "..." if len(highest_avg['Merchant']) > 30 else highest_avg['Merchant'],
                f"${highest_avg['Avg']:.0f}"
            )
        
        with col4:
            total_merchants = len(merchant_totals)
            avg_per_merchant = merchant_totals['Total'].mean()
            st.metric(
                "🏪 Total Merchants",
                total_merchants,
                f"${avg_per_merchant:.0f} avg"
            )
        
        st.divider()
        
        # Row 1: Top 10 spending breakdown
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("**🏅 Top 10 Merchants by Total Spending**")
            top_10 = merchant_totals.head(10)
            
            # Create a more detailed bar chart
            fig = go.Figure()
            
            # Add bars with gradient colors
            colors = ['#EF4444', '#F59E0B', '#F59E0B', '#FBBF24', '#FBBF24', 
                     '#FCD34D', '#FCD34D', '#FDE68A', '#FDE68A', '#FEF3C7']
            
            fig.add_trace(go.Bar(
                y=top_10['Merchant'],
                x=top_10['Total'],
                orientation='h',
                marker=dict(color=colors),
                text=[f"${x:.0f}" for x in top_10['Total']],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Total: $%{x:.2f}<extra></extra>'
            ))
            
            # Add visit count annotations
            for i, row in top_10.iterrows():
                fig.add_annotation(
                    x=row['Total'] * 0.05,
                    y=row['Merchant'],
                    text=f"🔄 {int(row['Visits'])}",
                    showarrow=False,
                    font=dict(color='white', size=10),
                    xanchor='left'
                )
            
            fig.update_layout(
                height=450,
                xaxis_title="Total Spending ($)",
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**⭐ Loyalty Score Ranking**")
            loyalty_top_10 = merchant_totals.sort_values('Loyalty Score', ascending=False).head(10)
            
            fig = go.Figure()
            
            # Create gradient from green to light green
            max_score = loyalty_top_10['Loyalty Score'].max()
            colors_loyalty = [f'rgba(16, 185, 129, {0.5 + (score/max_score)*0.5})' 
                            for score in loyalty_top_10['Loyalty Score']]
            
            fig.add_trace(go.Bar(
                y=loyalty_top_10['Merchant'],
                x=loyalty_top_10['Loyalty Score'],
                orientation='h',
                marker=dict(color=colors_loyalty),
                text=[f"{x:.0f}" for x in loyalty_top_10['Loyalty Score']],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<br>Visits: %{customdata[0]}<br>Total: $%{customdata[1]:.0f}<extra></extra>',
                customdata=loyalty_top_10[['Visits', 'Total']].values
            ))
            
            fig.update_layout(
                height=450,
                xaxis_title="Loyalty Score",
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Loyalty Score** = Visits × Total Spend / 100\n\nHigher score = More frequent + More expensive")
        
        # Row 2: Spending trends over time
        st.markdown("**📈 Top 10 Merchants - Spending Timeline**")
        
        # Add selector for visualization type
        col1, col2 = st.columns([3, 1])
        with col2:
            chart_type = st.radio("Chart Type:", ["Line", "Area", "Scatter"], horizontal=True, key="merchant_chart_type")
        
        top_10_merchants = merchant_totals.head(10)['Merchant'].tolist()
        merchant_timeline = merchant_df[merchant_df['Description'].isin(top_10_merchants)]
        merchant_daily = merchant_timeline.groupby(['Date', 'Description'])['Amount'].sum().reset_index()
        
        if chart_type == "Line":
            fig = px.line(merchant_daily, x='Date', y='Amount', color='Description',
                         markers=True, height=400)
        elif chart_type == "Area":
            fig = px.area(merchant_daily, x='Date', y='Amount', color='Description', height=400)
        else:  # Scatter
            fig = px.scatter(merchant_daily, x='Date', y='Amount', color='Description',
                           size='Amount', height=400)
        
        fig.update_layout(hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig, use_container_width=True)
        
        # Row 3: Detailed patterns
        st.markdown("**� Detailed Merchant Patterns**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("*Visit Frequency Heatmap (Top 10)*")
            merchant_dow = merchant_df.groupby(['Description', 'DayOfWeek']).size().reset_index(name='Count')
            top_10_list = merchant_totals.head(10)['Merchant'].tolist()
            merchant_dow_filtered = merchant_dow[merchant_dow['Description'].isin(top_10_list)]
            
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot = merchant_dow_filtered.pivot(index='Description', columns='DayOfWeek', values='Count').fillna(0)
            pivot = pivot.reindex(columns=[d for d in day_order if d in pivot.columns])
            
            # Reorder by total visits
            pivot['Total'] = pivot.sum(axis=1)
            pivot = pivot.sort_values('Total', ascending=False).drop('Total', axis=1)
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='Blues',
                text=pivot.values,
                texttemplate='%{text:.0f}',
                textfont={"size": 10},
                hovertemplate='<b>%{y}</b><br>%{x}<br>Visits: %{z}<extra></extra>'
            ))
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("*Spending Distribution by Merchant*")
            
            # Create a sunburst chart showing category > merchant breakdown
            if 'Category' in merchant_df.columns:
                top_10_with_cat = merchant_df[merchant_df['Description'].isin(top_10_list)].copy()
                sunburst_data = top_10_with_cat.groupby(['Category', 'Description'])['Amount'].sum().reset_index()
                
                fig = px.sunburst(
                    sunburst_data,
                    path=['Category', 'Description'],
                    values='Amount',
                    height=450,
                    color='Amount',
                    color_continuous_scale='RdYlGn_r'
                )
                fig.update_traces(textinfo='label+percent entry')
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback: Average ticket size
                st.markdown("*Average Transaction Size (Top 10)*")
                avg_ticket = merchant_totals.head(10)[['Merchant', 'Avg', 'Visits']].sort_values('Avg', ascending=False)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=avg_ticket['Merchant'],
                    x=avg_ticket['Avg'],
                    orientation='h',
                    marker=dict(
                        color=avg_ticket['Avg'],
                        colorscale='Oranges',
                        showscale=True
                    ),
                    text=[f"${x:.0f}" for x in avg_ticket['Avg']],
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Avg: $%{x:.2f}<br>Visits: %{customdata}<extra></extra>',
                    customdata=avg_ticket['Visits']
                ))
                fig.update_layout(
                    height=450,
                    xaxis_title="Average Transaction ($)",
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Bottom: Comprehensive merchant table
        st.markdown("**📋 Complete Merchant Analysis Table**")
        
        # Create a rich dataframe with all metrics
        merchant_table = merchant_totals.head(20).copy()
        merchant_table['Total'] = merchant_table['Total'].apply(lambda x: f"${x:.2f}")
        merchant_table['Avg'] = merchant_table['Avg'].apply(lambda x: f"${x:.2f}")
        merchant_table['Visits'] = merchant_table['Visits'].astype(int)
        merchant_table['Loyalty Score'] = merchant_table['Loyalty Score'].apply(lambda x: f"{x:.1f}")
        
        # Calculate spend percentage (based on actual merchant spending, not including payments)
        total_merchant_spend = merchant_df['Amount'].sum()
        merchant_totals['Spend %'] = (merchant_totals['Total'] / total_merchant_spend * 100).round(1)
        merchant_table['Spend %'] = merchant_totals.head(20)['Spend %'].apply(lambda x: f"{x:.1f}%")
        
        merchant_table = merchant_table.reset_index(drop=True)
        merchant_table.index = merchant_table.index + 1
        
        st.dataframe(
            merchant_table[['Merchant', 'Total', 'Visits', 'Avg', 'Spend %', 'Loyalty Score']],
            use_container_width=True,
            height=400
        )
        
    else:
        st.info("No merchant data available")

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
    transaction_type = st.selectbox("Transaction Type", ["All", "Expenses (Negative)", "Payments/Credits (Positive)"])

with col3:
    sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High to Low)", "Amount (Low to High)"])

# Apply search and filters
display_df = filtered_df.copy()

if search_term:
    display_df = display_df[display_df['Description'].str.contains(search_term, case=False, na=False)]

if transaction_type == "Expenses (Negative)":
    display_df = display_df[display_df['Amount'] < 0]
elif transaction_type == "Payments/Credits (Positive)":
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

# Format the display - keep Amount as numeric for proper sorting
display_df_formatted = display_df.copy()
display_df_formatted['Date'] = display_df_formatted['Date'].dt.strftime('%Y-%m-%d')
# Keep Amount as float but use column_config to format display

st.dataframe(
    display_df_formatted, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Amount": st.column_config.NumberColumn(
            "Amount",
            format="$%.2f",
            help="Transaction amount"
        ),
        "Date": st.column_config.TextColumn(
            "Date",
            help="Transaction date"
        )
    }
)

# Export option
st.download_button(
    label="📥 Download Transactions as CSV",
    data=display_df.to_csv(index=False).encode('utf-8'),
    file_name=f"transactions_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
