import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from tkcalendar import DateEntry
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Database setup
conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS expenses
             (date TEXT, category TEXT, description TEXT, amount REAL)''')
conn.commit()
conn.close()

# Main window
root = tk.Tk()
root.title('Expense Tracker')
root.geometry('600x500')  # Increased height for total field

# Create frames for layout
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

table_frame = tk.Frame(root)
table_frame.pack(pady=10)

# Labels and input fields
tk.Label(input_frame, text='Date:').grid(row=0, column=0, padx=5, pady=5)
date_entry = DateEntry(input_frame, width=16, background='darkblue', foreground='white', borderwidth=2,
                       date_pattern='yyyy-mm-dd')
date_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(input_frame, text='Category:').grid(row=1, column=0, padx=5, pady=5)
category_var = tk.StringVar()
categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Other',
              'Home Expenses', 'Agriculture', 'Investment', 'Education']
category_menu = ttk.Combobox(input_frame, textvariable=category_var, values=categories)
category_menu.grid(row=1, column=1, padx=5, pady=5)

tk.Label(input_frame, text='Description:').grid(row=2, column=0, padx=5, pady=5)
description_entry = tk.Entry(input_frame)
description_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(input_frame, text='Amount: in ₹').grid(row=3, column=0, padx=5, pady=5)
amount_entry = tk.Entry(input_frame)
amount_entry.grid(row=3, column=1, padx=5, pady=5)

# Month names for filtering
tk.Label(input_frame, text='Month:').grid(row=5, column=0, padx=5, pady=5)
month_var = StringVar()
months = ['All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']
month_menu = ttk.Combobox(input_frame, textvariable=month_var, values=months)
month_menu.grid(row=5, column=1, padx=5, pady=5)
month_menu.current(0)  # Default to 'All'


# Function to add expense
def add_expense():
    date = date_entry.get()
    category = category_var.get()
    description = description_entry.get()
    amount = amount_entry.get()

    if not date or not category or not description or not amount:
        messagebox.showwarning("Input Error", "All fields are required!")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Input Error", "Amount should be a number!")
        return

    # Add the expense to the SQLite database
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)',
                   (date, category, description, amount))
    conn.commit()
    conn.close()
    load_expenses()  # Reload the table
    clear_entries()


# Function to clear input fields
def clear_entries():
    description_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)


# Add expense button
add_button = tk.Button(input_frame, text='Add Expense', command=add_expense)
add_button.grid(row=6, column=1, padx=5, pady=5)

# Table to display expenses
expense_table = ttk.Treeview(table_frame, columns=('Date', 'Category', 'Description', 'Amount'), show='headings')
expense_table.heading('Date', text='Date')
expense_table.heading('Category', text='Category')
expense_table.heading('Description', text='Description')
expense_table.heading('Amount', text='Amount in ₹')
expense_table.pack()

# Total Label
total_label = tk.Label(root, text="Total: ₹ 0.00", font=("Arial", 12, "bold"))
total_label.pack(pady=10)


# Helper function to map month names to numbers
def get_month_number(month_name):
    months_mapping = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04',
        'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12'
    }
    return months_mapping.get(month_name)


# Load expenses into a table, filtered by month, and calculate total
def load_expenses():
    month = month_var.get()

    for row in expense_table.get_children():
        expense_table.delete(row)

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    if month == 'All':
        cursor.execute('SELECT * FROM expenses')
    else:
        month_number = get_month_number(month)
        cursor.execute("SELECT * FROM expenses WHERE strftime('%m', date) = ?", (month_number,))

    expenses = cursor.fetchall()
    conn.close()

    total_amount = 0  # Variable to store total expenses

    for expense in expenses:
        expense_table.insert('', 'end', values=expense)
        total_amount += expense[3]  # Add the expense amount to total

    # Update total label with the calculated total
    total_label.config(text=f"Total: ₹ {total_amount:.2f}")


# Initially load expenses
load_expenses()


# Function to generate an Excel report with total calculation
def generate_report():
    conn = sqlite3.connect('expenses.db')
    df = pd.read_sql_query('SELECT * FROM expenses', conn)
    conn.close()

    if df.empty:
        messagebox.showwarning("No Data", "No expenses to generate a report!")
        return

    # Grouping expenses by category and calculating totals
    report_df = df.groupby('category')['amount'].sum().reset_index()
    report_df['amount'] = report_df['amount'].apply(lambda x: f'₹ {x:.2f}')

    # Adding total row
    total_amount = df['amount'].sum()
    total_row = pd.DataFrame({'category': ['Total'], 'amount': [f'₹ {total_amount:.2f}']})
    report_df = pd.concat([report_df, total_row], ignore_index=True)

    # Save report as Excel
    report_df.to_excel('Expense_Report.xlsx', index=False)

    messagebox.showinfo("Report Generated", "Expense report saved as 'Expense_Report.xlsx'.")


# Function to visualize spending by category, filtered by month
def visualize_expenses():
    month = month_var.get()

    conn = sqlite3.connect('expenses.db')

    if month == 'All':
        df = pd.read_sql_query('SELECT category, SUM(amount) as total FROM expenses GROUP BY category', conn)
    else:
        month_number = get_month_number(month)
        query = "SELECT category, SUM(amount) as total FROM expenses WHERE strftime('%m', date) = ? GROUP BY category"
        df = pd.read_sql_query(query, conn, params=(month_number,))

    conn.close()

    if df.empty:
        messagebox.showwarning("No Data", "No expenses to visualize for the selected month!")
        return

    # Plotting the data
    plt.figure(figsize=(6, 6))
    plt.pie(df['total'], labels=df['category'], autopct='%1.1f%%', startangle=140)
    plt.title(f'Spending by Category for {month}' if month != 'All' else 'Spending by Category')
    plt.show()


# Add buttons for generating report and visualization
report_button = tk.Button(root, text='Generate Report', command=generate_report)
report_button.pack(pady=5)

visualize_button = tk.Button(root, text='Visualize Expenses', command=visualize_expenses)
visualize_button.pack(pady=5)


# Function to update the expense table and total when the month is changed
def update_on_month_change(*args):
    load_expenses()


# Trigger load_expenses when the month selection is changed
month_var.trace('w', update_on_month_change)

root.mainloop()
