from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def load_assets():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_assets(assets):
    with open("data.json", "w") as f:
        json.dump(assets, f, indent=4)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def get_asset_counts():
    assets = load_assets()
    return {
        'total': len(assets),
        'active': sum(1 for a in assets if a['status'] == 'Active'),
        'repair': sum(1 for a in assets if a['status'] == 'In Repair'),
        'retired': sum(1 for a in assets if a['status'] == 'Retired')
    }

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['user'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    counts = get_asset_counts()
    return render_template('dashboard.html', **counts)

@app.route('/add', methods=['GET', 'POST'])
def add_asset():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        asset = {
            "id": len(load_assets()) + 1,
            "name": request.form['name'],
            "type": request.form['type'],
            "location": request.form['location'],
            "assigned_to": request.form['assigned_to'],
            "status": request.form['status'],
            "serial_no": request.form['serial_no'],
            "date_added": datetime.now().strftime("%Y-%m-%d")
        }
        assets = load_assets()
        assets.append(asset)
        save_assets(assets)
        flash('Asset added successfully!', 'success')
        return redirect(url_for('view_assets'))
    return render_template('add_asset.html')

@app.route('/view')
def view_assets():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    status_filter = request.args.get('status')
    assets = load_assets()
    
    if status_filter:
        assets = [asset for asset in assets if asset['status'] == status_filter]
    
    counts = get_asset_counts()
    return render_template('view_assets.html', 
                         assets=assets, 
                         current_filter=status_filter,
                         **counts)

@app.route('/delete/<int:asset_id>')
def delete_asset(asset_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    assets = [a for a in load_assets() if a['id'] != asset_id]
    save_assets(assets)
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('view_assets'))

@app.route('/update/<int:asset_id>', methods=['GET', 'POST'])
def update_asset(asset_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    assets = load_assets()
    asset = next((a for a in assets if a['id'] == asset_id), None)
    
    if not asset:
        flash('Asset not found!', 'danger')
        return redirect(url_for('view_assets'))
    
    if request.method == 'POST':
        asset.update({
            "name": request.form['name'],
            "type": request.form['type'],
            "location": request.form['location'],
            "serial_no": request.form['serial_no'],
            "assigned_to": request.form['assigned_to'],
            "status": request.form['status']
        })
        save_assets(assets)
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('view_assets'))
    
    return render_template('update_asset.html', asset=asset)

@app.route('/track', methods=['GET', 'POST'])
def track_asset():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    assets = []
    search_type = 'name'  # Default search type
    search_term = ''
    
    if request.method == 'POST' or request.args.get('name'):
        search_term = request.form.get('name') or request.args.get('name')
        assets_data = load_assets()
        
        # Determine if searching by serial number (if input is numeric)
        if search_term.isdigit():
            search_type = 'serial'
            assets = [a for a in assets_data if str(a['serial_no']) == search_term]
        else:
            search_type = 'name'
            # Search by asset name (partial match)
            assets_by_name = [a for a in assets_data if search_term.lower() in a['name'].lower()]
            # Search by assigned user (partial match)
            assets_by_user = [a for a in assets_data if search_term.lower() in a['assigned_to'].lower()]
            # Combine results, removing duplicates
            assets = list({a['id']: a for a in assets_by_name + assets_by_user}.values())
    
    return render_template('track_asset.html', 
                         assets=assets,
                         search_term=search_term,
                         search_type=search_type)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)