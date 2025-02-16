# SportsBettingARB

**SportsBettingARB** is a Python-based application that uses the Odds API to identify arbitrage opportunities between a primary sportsbook and a polymarket. It helps users find profitable betting scenarios where differences in odds between these sources guarantee a risk-free profit.

---

## 🛠️ **Setup Instructions**

### 1️⃣ **Clone the Repository**
```bash
git clone https://github.com/PragalvhaSharma/SportsBettingARB.git
cd SportsBettingARB
```

### 2️⃣ **Create a Virtual Environment (Optional but Recommended)**
```bash
python -m venv venv
# Activate on Mac/Linux
source venv/bin/activate

# Activate on Windows
.\venv\Scripts\activate
```

### 3️⃣ **Install Required Dependencies**
```bash
pip install -r requirements.txt
```

---

## 🚀 **Running the Application**

### **Step 1: Start the Server**
```bash
cd server
python main.py
```
The server will start, and you should see a message indicating it's running locally (e.g., `http://localhost:5000`).

### **Step 2: Run the Main Script**
Open a new terminal (with the virtual environment still active) and run:
```bash
python main.py
```

The application will start processing odds data and display arbitrage opportunities in the terminal or in the `arbOutput` directory.

---

## ⚙️ **How It Works**

1. **Data Collection:** The app fetches odds data from the Odds API, comparing lines between a primary sportsbook and the polymarket.
2. **Arbitrage Detection:** It applies formulas to identify discrepancies where betting on both sides ensures a profit.
3. **Output Generation:** Profitable opportunities are logged into the `arbOutput` directory.

---

## 📂 **Project Structure**
```
.
├── arbOutput             # Contains arbitrage opportunity results
├── jsonOutputs           # Stores raw JSON outputs from the API
├── nba                    # NBA-specific betting insights
├── secondaryMarkets       # Data for secondary betting markets
├── server                 # Server-related files
├── IdeasTo-Implement.txt  # Future feature ideas
├── main.py                # Primary script to run after starting the server
├── requirements.txt       # Python dependencies
└── README.md              # This documentation
```

---

## 🧠 **Key Concepts**
- **Arbitrage Betting**: Simultaneously betting on all outcomes of an event using different bookmakers to guarantee a profit.
- **Odds API**: Used to fetch live odds data.
- **Polymarket vs Primary Sportsbook**: The script compares a decentralized prediction market with a traditional sportsbook to find discrepancies.

---

## 🔍 **Troubleshooting**

1. **Dependency Issues**: Run `pip install --upgrade pip` and reinstall the dependencies.
2. **API Issues**: Ensure the Odds API key is correctly configured in the environment variables.
3. **Output Errors**: Check the `arbOutput` directory for logs.

---

## 🌱 **Future Improvements**
- 🖥️ GUI Interface for easier usage.
- ⚙️ Support for additional sportsbooks.
- 📈 Enhanced performance with parallel API calls.

---

**Happy Arbitrage Hunting! 🏆**

