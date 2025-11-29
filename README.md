# 💳 Smart Budget Tracker - Personal Finance Manager

A powerful, intelligent budget tracking application that automatically parses credit card and bank statements (PDF) from multiple financial institutions, providing comprehensive spending analytics, trend analysis, and budget management tools.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-FF4B4B.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Features

### 📄 Multi-Institution PDF Parsing
- **9 Financial Institutions Supported:**
  - Chase (Prime Visa, Amazon Card)
  - Apple Card
  - Discover
  - Bank of America (Cash Rewards, Premium Rewards, Travel Rewards)
  - American Express (Cash Magnet, Gold, Platinum, Blue Cash)
  - Capital One (VentureOne, Venture X, Quicksilver, Savor)
  - Barclays (Frontier Airlines, JetBlue, Wyndham, Aviator)
  - Digital Federal Credit Union (DCU) - Checking & Savings
  - Lowe's/Synchrony Bank (Store Cards)

- **Intelligent Extraction:**
  - Card name and last 4 digits
  - Statement balance and available credit
  - Minimum payment and due date
  - Credit limit for utilization tracking
  - Transaction history with dates, descriptions, and amounts

### 💰 Advanced Financial Analytics

#### 📊 9-Metric Dashboard
- Total Income & Expenses
- Net Balance with trend indicators
- Average Daily Spend
- Transaction Count
- Projected Monthly Spend
- Largest Single Expense
- Savings Rate (%)
- Daily Burn Rate
- Credit Utilization per card

#### 📈 4-Tab Visualization System

**1. Overview Tab:**
- Daily spending with 3 moving averages (3-day, 7-day, 14-day)
- Cumulative spending tracker with velocity metrics
- Category trends over time (stacked area chart)
- Smart trend detection (alerts if spending up/down >10%)

**2. Time Patterns Tab:**
- Day of week analysis
- Weekday vs weekend comparison
- Spending heatmap by week and day
- Identifies your highest/lowest spending days

**3. Categories Tab:**
- Category distribution pie chart
- Top 10 merchants bar chart
- Detailed category breakdown table
- Transaction counts and averages per category

**4. Cards Tab:**
- Spending distribution by card
- Card usage timeline
- Side-by-side card comparison
- Individual card performance metrics

### 🎯 Budget Management
- Set monthly budget limits per category
- Real-time progress tracking with visual indicators
- Budget performance summary
- Daily allowance calculator
- Over-budget category alerts
- Budget vs actual comparison

### 🔍 Smart Features
- **Duplicate Detection:** Automatically identifies and filters duplicate transactions
- **Multi-PDF Upload:** Process multiple statements simultaneously
- **Auto Date Range:** Automatically detects transaction date range
- **Foreign Currency Support:** Handles USD-converted international transactions
- **Miles/Points Tracking:** Extracts loyalty program data (Barclays)
- **Due Date Alerts:** Color-coded warnings for upcoming/overdue payments
- **Transaction Categorization:** AI-powered categorization into 15+ categories

### 🎨 Modern UI/UX
- Responsive wide layout
- Custom styled tabs with blue accent theme
- Enhanced metric cards
- Professional color palette
- Smooth hover effects
- Mobile-friendly design

---

## 🛠️ Technology Stack

### Core Framework
- **[Streamlit 1.50.0](https://streamlit.io/)** - Web application framework
  - Rapid prototyping and deployment
  - Built-in widgets and state management
  - Interactive data visualization support

### Data Processing
- **[Pandas 2.3.3](https://pandas.pydata.org/)** - Data manipulation and analysis
  - DataFrame operations for transaction management
  - Date/time handling and aggregations
  - Data filtering and grouping

- **[pdfplumber 0.11.8](https://github.com/jsvine/pdfplumber)** - PDF text extraction
  - Robust text parsing from various PDF formats
  - Table detection and extraction
  - Layout-aware text extraction

### Visualization
- **[Plotly 6.5.0](https://plotly.com/python/)** - Interactive charts
  - `plotly.express` - High-level charting interface
  - `plotly.graph_objects` - Low-level customizable charts
  - Bar charts, line charts, area charts, pie charts, heatmaps
  - Hover interactions and zoom capabilities

### Additional Libraries
- **re (Regular Expressions)** - Pattern matching for statement parsing
- **datetime** - Date/time manipulation and calculations

---

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone https://github.com/ss2638/budget.git
cd budget
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### requirements.txt
```txt
streamlit==1.50.0
pandas==2.3.3
pdfplumber==0.11.8
plotly==6.5.0
```

---

## 🚀 Deployment

### Local Deployment

#### Option 1: Using Streamlit CLI
```bash
streamlit run budget_tracker.py
```

The app will open automatically at `http://localhost:8501`

#### Option 2: Using Python Module
```bash
python -m streamlit run budget_tracker.py
```

#### Custom Port
```bash
streamlit run budget_tracker.py --server.port 8080
```

### Production Deployment

#### Streamlit Community Cloud (Recommended)
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Select `budget_tracker.py` as the main file
5. Deploy!

**Configuration:** Create `.streamlit/config.toml`
```toml
[theme]
primaryColor = "#3B82F6"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F1F5F9"
textColor = "#1E293B"
font = "sans serif"

[server]
maxUploadSize = 200
enableXsrfProtection = true
```

#### Heroku Deployment
```bash
# Create Procfile
echo "web: streamlit run budget_tracker.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# Create setup.sh
cat > setup.sh << 'EOF'
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
EOF

# Deploy
heroku create your-app-name
git push heroku main
```

#### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY budget_tracker.py .

EXPOSE 8501

CMD ["streamlit", "run", "budget_tracker.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t budget-tracker .
docker run -p 8501:8501 budget-tracker
```

---

## 📖 Usage Guide

### 1. Upload Statements
- Click **"Browse files"** in the sidebar
- Select one or more PDF statements
- Supports multiple statements from different institutions

### 2. View Credit Card Overview
- See all your cards with balances and due dates
- Color-coded alerts for overdue payments
- Credit utilization warnings (>30% = warning, >70% = danger)

### 3. Analyze Spending
- Navigate through 4 tabs of detailed analytics
- Adjust date range filters in sidebar
- Filter by categories or specific cards

### 4. Set Budget Goals
- Use sidebar to set monthly budget per category
- Track progress with visual indicators
- Monitor daily allowance and projected spend

### 5. Review Transactions
- Scroll to bottom for detailed transaction table
- Sortable by date, amount, category, or card
- Search/filter capabilities

---

## 🧪 Supported Statement Formats

### Chase
- **Pattern:** "Account Number: XXXX XXXX XXXX 4860"
- **Balance:** "New Balance $994.09"
- **Transactions:** "MM/DD Description $Amount"

### Apple Card
- **Pattern:** "Your October Balance... $488.49 $243.15 Nov 30, 2025"
- **Due Date:** "Payment Due By Nov 30, 2025"
- **Transactions:** "MM/DD Merchant Location $Amount"

### Discover
- **Pattern:** "NewBalance MinimumPayment PaymentDueDate"
- **Transactions:** "MM/DD Merchant $Amount"

### Bank of America
- **Cards:** Cash Rewards, Premium Rewards, Travel Rewards
- **Pattern:** "New Balance: $XXX.XX"
- **Transactions:** "MM/DD Description $Amount"

### American Express
- **Pattern:** "Account Ending5-05001"
- **Transactions:** "MM/DD/YY Description $Amount"
- **Multiple card support:** Cash Magnet, Gold, Platinum, Blue Cash

### Capital One
- **Pattern:** "ending in 6165"
- **Foreign Currency:** Handles INR with USD conversion
- **Transactions:** "MMM DD MMM DD Description $Amount"

### Barclays
- **Cards:** Frontier Airlines, JetBlue, Wyndham, Aviator
- **Miles Tracking:** Extracts miles/points earned
- **Transactions:** "MMM DD MMM DD Merchant $Amount Miles"

### DCU (Digital Federal Credit Union)
- **Accounts:** Free Checking, Primary Savings
- **Pattern:** "ACCT# X"
- **Transactions:** "MMMDD Description Amount Balance"
- **Format:** Withdrawals (negative), Deposits (positive)

### Synchrony Bank (Lowe's)
- **Pattern:** "Account Number ending in 698 0"
- **Balance:** "New Balance: $117.11"
- **Transactions:** "MM/DD Reference# Store Description $Amount"

---

## 🎯 Transaction Categories

The app automatically categorizes transactions into:
- 🍔 Food & Dining
- 🛒 Groceries
- ⛽ Gas & Transportation
- 🛍️ Shopping
- 🎬 Entertainment
- 💊 Healthcare
- 🏠 Home & Utilities
- ✈️ Travel
- 🎓 Education
- 💼 Professional Services
- 🏦 Finance & Banking
- 🚗 Automotive
- 💰 Income/Payments
- 🔧 Home Improvement
- 📱 Subscriptions
- ❓ Other

---

## 🔒 Security & Privacy

- **Local Processing:** All PDF parsing happens locally - no data sent to external servers
- **No Data Storage:** No transaction data is permanently stored
- **Session-Based:** Data exists only during your browser session
- **PDF Upload:** Files are processed in memory and not saved to disk

---

## 🐛 Troubleshooting

### PDF Not Parsing
- Ensure PDF is text-based (not scanned image)
- Check if institution is supported
- Verify PDF is not password-protected

### Missing Transactions
- Check if transactions are in a different date range
- Adjust date filters in sidebar
- Some promotional sections may not be parsed

### Credit Limit Issues
- Ensure "Credit Limit" appears in statement
- Check if limit is on same line as "Available Credit"
- Some cards don't report limits on statements

### Duplicate Transactions
- App automatically detects duplicates
- Based on: same date, description, amount, and card
- Check debug info expander if needed

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Adding New Institution Support
To add support for a new bank/card:
1. Add detection pattern in `extract_transactions_from_pdf()`
2. Add account number extraction pattern
3. Add balance parsing logic
4. Add transaction parsing pattern
5. Test with sample statements

---

## 📝 Roadmap

- [ ] Machine learning for improved categorization
- [ ] Expense forecasting and predictions
- [ ] Bill reminder notifications
- [ ] Export to Excel/CSV
- [ ] Multiple currency support
- [ ] Monthly comparison reports
- [ ] Savings goals tracking
- [ ] Subscription detection and management
- [ ] Receipt OCR integration
- [ ] Mobile app version

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- PDF parsing powered by [pdfplumber](https://github.com/jsvine/pdfplumber)
- Visualizations by [Plotly](https://plotly.com/)
- Data processing with [Pandas](https://pandas.pydata.org/)

---

## 📧 Contact

**Shivaneeth Raj Siliveru**
- GitHub: [@ss2638](https://github.com/ss2638)
- Repository: [budget](https://github.com/ss2638/budget)

---

## 🎉 Screenshots

### Dashboard Overview
![Dashboard](screenshots/dashboard.png)

### Credit Card Management
![Cards](screenshots/cards.png)

### Spending Analytics
![Analytics](screenshots/analytics.png)

### Budget Tracking
![Budget](screenshots/budget.png)

---

**⭐ If you find this project helpful, please consider giving it a star!**

---

*Last Updated: November 29, 2025*
