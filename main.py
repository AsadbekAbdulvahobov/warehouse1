from flask import Flask, render_template, request, redirect, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Fayl nomlari
WAREHOUSE_FILE = 'warehouse.json'
REPORT_FILE = 'monthly_report.json'
TOTAL_TAKEN_FILE = 'total_taken.json'

# JSON fayldan ma'lumotlarni yuklash
def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

# JSON faylga ma'lumotlarni yozish
def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

# Ombor, hisobot va jami ma'lumotlar
warehouse = load_data(WAREHOUSE_FILE)
report = load_data(REPORT_FILE)
total_taken = load_data(TOTAL_TAKEN_FILE)

@app.route('/')
def home():
    return render_template('index.html', warehouse=warehouse)

@app.route('/add', methods=['POST'])
def add_item():
    item = request.form['item']
    quantity = int(request.form['quantity'])

    # Ombor ma'lumotlarini yangilash
    warehouse[item] = warehouse.get(item, 0) + quantity
    save_data(WAREHOUSE_FILE, warehouse)

    message = f"'{item}' mahsuloti {quantity} miqdorda qo'shildi."
    return render_template('index.html', warehouse=warehouse, message=message)

@app.route('/filter', methods=['GET'])
def filter_products():
    filter_type = request.args.get('filter')

    low_stock = {}
    high_stock = {}

    if filter_type == 'low':
        low_stock = {item: quantity for item, quantity in warehouse.items() if quantity < 50}
    elif filter_type == 'high':
        high_stock = {item: quantity for item, quantity in warehouse.items() if quantity > 500}

    return render_template(
        'index.html',
        warehouse=warehouse,
        low_stock=low_stock if filter_type == 'low' else None,
        high_stock=high_stock if filter_type == 'high' else None
    )

@app.route('/edit/<item>', methods=['GET', 'POST'])
def edit_item(item):
    if request.method == 'POST':
        new_quantity = request.form['quantity']

        if new_quantity.isdigit():
            new_quantity = int(new_quantity)
            old_quantity = warehouse.get(item, 0)

            if new_quantity > old_quantity:
                error = f"{item} mahsulotdan buncha miqdor mavjud emas!"
                return render_template('edit.html', item=item, old_quantity=old_quantity, error=error)
            else:
                warehouse[item] = old_quantity - new_quantity
                save_data(WAREHOUSE_FILE, warehouse)

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if item not in report:
                    report[item] = []
                report[item].append({'date': timestamp, 'quantity_removed': new_quantity})
                save_data(REPORT_FILE, report)

                if item not in total_taken:
                    total_taken[item] = new_quantity
                else:
                    total_taken[item] += new_quantity
                save_data(TOTAL_TAKEN_FILE, total_taken)

                return redirect('/')
        else:
            error = "Miqdorni to'g'ri kiriting!"
            return render_template('edit.html', item=item, error=error)

    old_quantity = warehouse.get(item, 0)
    return render_template('edit.html', item=item, old_quantity=old_quantity)

@app.route('/view_reports', methods=['GET'])
def view_reports():
    report_type = request.args.get('type')

    if report_type == 'monthly':
        return render_template('index.html', warehouse=warehouse, report=report)
    elif report_type == 'total':
        return render_template('index.html', warehouse=warehouse, total_taken=total_taken)

    return render_template('index.html', warehouse=warehouse)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(warehouse)

@app.route('/api/report', methods=['GET'])
def get_report():
    return jsonify(report)

@app.route('/api/total_taken', methods=['GET'])
def get_total_taken():
    return jsonify(total_taken)

if __name__ == '__main__':
    app.run(debug=True)
