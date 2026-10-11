from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shreshtha Aahar - Babai Hotel Manager",
    page_icon="🍛",
    layout="wide",
)

# --- DATABASE SETUP ---
DB_NAME = "babai_hotel.db"


def get_connection():
  conn = sqlite3.connect(DB_NAME, check_same_thread=False)
  return conn


def init_db():
  conn = get_connection()
  cursor = conn.cursor()

  # Sales Table
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            walk_in REAL,
            online REAL
        )
    """
  )

  # Expenses Table
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            notes TEXT
        )
    """
  )

  # Categories Table
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """
  )
  conn.commit()

  # Insert Default Categories if missing
  default_categories = [
      "Salaries",
      "Vegetables",
      "Gas",
      "Rent",
      "Maintenance",
      "Water Bottles",
      "Bore Water Supplier",
      "R.O. Water Supplier",
      "Banana Leafs",
      "Coconuts",
      "Dairy",
      "Milk",
      "Paneer",
      "Rapido",
      "Instacart",
      "Fruits",
      "New Material",
      "Savings",
      "Misc",
      "Groceries",
  ]
  for cat in default_categories:
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
  conn.commit()
  conn.close()


init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🍛 Babai Hotel Portal")
st.sidebar.markdown("### Shreshtha Aahar Operations")
menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard & Analytics",
        "💰 Record Sales",
        "OUT️ Record Expenses",
        "📂 Manage Categories",
        "📋 View All Records",
    ],
)

conn = get_connection()

# --- 1. DASHBOARD & ANALYTICS ---
if menu == "📊 Dashboard & Analytics":
  st.title("📊 Shreshtha Aahar - Financial Dashboard")
  st.markdown("Overview of sales, expenses, and profitability.")

  # Load data
  df_sales = pd.read_sql("SELECT * FROM sales", conn)
  df_expenses = pd.read_sql("SELECT * FROM expenses", conn)

  if not df_sales.empty or not df_expenses.empty:
    # Date filters
    col1, col2 = st.columns(2)
    with col1:
      start_date = st.date_input("Start Date", date(2026, 1, 1))
    with col2:
      end_date = st.date_input("End Date", date.today())

    # Filter logic
    if not df_sales.empty:
      df_sales["date"] = pd.to_datetime(df_sales["date"])
      mask_sales = (df_sales["date"].dt.date >= start_date) & (
          df_sales["date"].dt.date <= end_date
      )
      filtered_sales = df_sales.loc[mask_sales]
    else:
      filtered_sales = pd.DataFrame(columns=["date", "walk_in", "online"])

    if not df_expenses.empty:
      df_expenses["date"] = pd.to_datetime(df_expenses["date"])
      mask_exp = (df_expenses["date"].dt.date >= start_date) & (
          df_expenses["date"].dt.date <= end_date
      )
      filtered_expenses = df_expenses.loc[mask_exp]
    else:
      filtered_expenses = pd.DataFrame(
          columns=["date", "category", "amount", "notes"]
      )

    # Calculate Totals
    total_walkin = (
        filtered_sales["walk_in"].sum() if not filtered_sales.empty else 0
    )
    total_online = (
        filtered_sales["online"].sum() if not filtered_sales.empty else 0
    )
    total_sales = total_walkin + total_online
    total_expenses = (
        filtered_expenses["amount"].sum() if not filtered_expenses.empty else 0
    )
    net_profit = total_sales - total_expenses

    # Metrics Display
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Sales", f"₹ {total_sales:,.2f}")
    m2.metric("Total Expenses", f"₹ {total_expenses:,.2f}")
    m3.metric(
        "Net Profit",
        f"₹ {net_profit:,.2f}",
        delta=f"₹ {net_profit:,.2f}",
        delta_color="normal",
    )
    m4.metric(
        "Walk-in vs Online",
        f"W: ₹{total_walkin:,.0f}",
        f"O: ₹{total_online:,.0f}",
    )

    st.markdown("---")

    # Visualizations
    col_a, col_b = st.columns(2)

    with col_a:
      st.subheader("💡 Sales Breakdown")
      if total_sales > 0:
        sales_df = pd.DataFrame({
            "Channel": ["Walk-in", "Online"],
            "Amount": [total_walkin, total_online],
        })
        st.bar_chart(sales_df.set_index("Channel"))
      else:
        st.info("No sales data available for this range.")

    with col_b:
      st.subheader("💸 Expenses by Category")
      if not filtered_expenses.empty:
        exp_grouped = filtered_expenses.groupby("category")[
            "amount"
        ].sumDescr = filtered_expenses.groupby("category")["amount"].sum()
        st.bar_chart(exp_grouped)
      else:
        st.info("No expense data available for this range.")

  else:
    st.warning(
        "No records found in the database yet. Please start adding sales and"
        " expenses using the sidebar!"
    )

# --- 2. RECORD SALES ---
elif menu == "💰 Record Sales":
  st.title("💰 Record Daily Sales")
  st.markdown("Enter Walk-in and Online revenues for Babai Hotel.")

  with st.form("sales_form"):
    sale_date = st.date_input("Sale Date", date.today())
    walk_in = st.number_input(
        "Walk-in Sales (₹)", min_value=0.0, step=100.0, format="%.2f"
    )
    online = st.number_input(
        "Online Sales (Swiggy/Zomato) (₹)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
    )

    submitted = st.form_submit_button("Save Sales Entry")
    if submitted:
      cursor.execute(
          "INSERT INTO sales (date, walk_in, online) VALUES (?, ?, ?)",
          (str(sale_date), walk_in, online),
      )
      conn.commit()
      st.success("✅ Sales successfully recorded!")

# --- 3. RECORD EXPENSES ---
elif menu == "OUT️ Record Expenses":
  st.title("OUT️ Record Daily Expenses")
  st.markdown("Log operating expenses across your categories.")

  # Fetch current categories from DB
  categories_df = pd.read_sql("SELECT name FROM categories ORDER BY name", conn)
  category_list = categories_df["name"].tolist()

  with st.form("expense_form"):
    exp_date = st.date_input("Expense Date", date.today())
    category = st.selectbox("Expense Category", category_list)
    amount = st.number_input(
        "Amount (₹)", min_value=0.0, step=50.0, format="%.2f"
    )
    notes = st.text_input("Notes / Description (Optional)")

    submitted = st.form_submit_button("Save Expense Entry")
    if submitted:
      cursor.execute(
          "INSERT INTO expenses (date, category, amount, notes) VALUES (?,"
          " ?, ?, ?)",
          (str(exp_date), category, amount, notes),
      )
      conn.commit()
      st.success(
          f"✅ Expense of ₹{amount} under '{category}' successfully recorded!"
      )

# --- 4. MANAGE CATEGORIES ---
elif menu == "📂 Manage Categories":
  st.title("📂 Manage Expense Categories")
  st.markdown("Add new custom categories as your restaurant grows.")

  with st.form("new_cat_form"):
    new_cat = st.text_input("New Category Name")
    add_submitted = st.form_submit_button("Add Category")

    if add_submitted:
      if new_cat.strip() != "":
        try:
          cursor.execute(
              "INSERT INTO categories (name) VALUES (?)", (new_cat.strip(),)
          )
          conn.commit()
          st.success(
              f"✅ Category '{new_cat.strip()}' added successfully! You can now"
              " select it under Expenses."
          )
        except sqlite3.IntegrityError:
          st.warning("⚠️ This category already exists.")
      else:
        st.error("Please enter a valid category name.")

  st.subheader("Existing Categories List")
  categories_df = pd.read_sql("SELECT name FROM categories ORDER BY name", conn)
  st.dataframe(categories_df, use_container_width=True)

# --- 5. VIEW ALL RECORDS ---
elif menu == "📋 View All Records":
  st.title("📋 Detailed Database Records")

  tab1, tab2 = st.tabs(["Sales Records", "Expense Records"])

  with tab1:
    st.subheader("All Sales Entries")
    df_sales = pd.read_sql("SELECT * FROM sales ORDER BY date DESC", conn)
    st.dataframe(df_sales, use_container_width=True)

    if not df_sales.empty:
      if st.button("Delete Selected Sale / Clear All"):
        # simple helper or download option
        pass

  with tab2:
    st.subheader("All Expense Entries")
    df_expenses = pd.read_sql("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(df_expenses, use_container_width=True)

conn.close()