from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.db import get_db
from datetime import datetime, timedelta
from bson.son import SON
import base64
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

# ------------------ HOME --------------------
@auth_bp.route('/')
def home():
    """Renders the home page."""
    return render_template('auth/home.html')

# ------------------ CUSTOMER --------------------
@auth_bp.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    """Handles customer registration."""
    db = get_db()
    if request.method == 'POST':
        # Basic validation for existing email/phone
        if db.customers.find_one({'email': request.form['email']}):
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('auth.customer_register'))
        if db.customers.find_one({'phone': request.form['phone']}):
            flash('An account with this phone number already exists.', 'danger')
            return redirect(url_for('auth.customer_register'))

        data = {
            "name": request.form['name'],
            "phone": request.form['phone'],
            "email": request.form['email'],
            "pin": request.form['pin'], # Storing PIN in plain text
            "address": {
                "flat_no": request.form['flat_no'],
                "street": request.form['street'],
                "landmark": request.form['landmark'],
                "city": request.form['city'],
                "state": request.form['state'],
                "pincode": request.form['pincode']
            }
        }
        db.customers.insert_one(data)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.customer_login'))
    return render_template('auth/customer_register.html')

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    """Handles customer login."""
    db = get_db()
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']
        user = db.customers.find_one({'phone': phone, 'pin': pin})
        if user:
            session['customer'] = str(user['_id']) # Store ObjectId as string in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('auth.customer_dashboard'))
        else:
            flash("Invalid phone number or PIN. Please try again.", 'danger')
    return render_template('auth/customer_login.html')

@auth_bp.route('/customer/dashboard')
def customer_dashboard():
    """Displays the customer dashboard with nearby stores."""
    if 'customer' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.customer_login'))

    db = get_db()
    customer = db.customers.find_one({'_id': ObjectId(session['customer'])})
    if not customer:
        session.pop('customer', None)
        flash('Your session is invalid. Please log in again.', 'danger')
        return redirect(url_for('auth.customer_login'))
    
    # Fetch all stores from the database
    stores = list(db.stores.find())
    
    return render_template('customer_dashboard.html', user=customer, stores=stores)

@auth_bp.route('/customer/profile')
def customer_profile():
    """Displays the customer's profile."""
    if 'customer' not in session:
        flash('Please log in to access your profile.', 'warning')
        return redirect(url_for('auth.customer_login'))

    db = get_db()
    customer = db.customers.find_one({'_id': ObjectId(session['customer'])})
    if not customer:
        session.pop('customer', None)
        flash('User profile not found. Please log in again.', 'danger')
        return redirect(url_for('auth.customer_login'))
    return render_template('customer_profile.html', user=customer)

@auth_bp.route('/customer/profile-data')
def api_customer_profile():
    """API endpoint to get customer profile data (JSON)."""
    if 'customer' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user = db.customers.find_one({'_id': ObjectId(session['customer'])}, {'_id': 0})
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404

# ------------------ MY ORDERS(In profile section) --------------------
@auth_bp.route('/customer/my-orders')
def my_orders():
    if 'customer' not in session:
        flash('Please log in to view your orders.', 'warning')
        return redirect(url_for('auth.customer_login'))

    db = get_db()
    customer_id = session['customer']

    # Fetch orders for this user
    orders = list(db.orders.find({'user_id': ObjectId(customer_id)}).sort("placed_at", -1))

    return render_template('auth/my_orders.html', orders=orders)

# ------------------ ADD TO CART --------------------
@auth_bp.route('/add-to-cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    db = get_db()
    product = db.items.find_one({"_id": ObjectId(product_id)})

    if not product:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Product not found!'}), 404
        flash('Product not found!', 'danger')
        return redirect(url_for('auth.customer_dashboard'))

    if 'cart' not in session:
        session['cart'] = []

    found_in_cart = False
    for item in session['cart']:
        if item['id'] == str(product['_id']):
            item['quantity'] += 1
            found_in_cart = True
            break
    
    if not found_in_cart:
        session['cart'].append({
            'id': str(product['_id']),
            'name': product['name'],
            'price': float(product['price']),
            'quantity': 1
        })

    session.modified = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'product_name': product['name'],
            'cart_count': len(session['cart'])
        })

    flash(f'"{product["name"]}" added to cart!', 'success')

    store_phone = product.get('store_phone')
    store = db.stores.find_one({'phone': store_phone})
    if store:
        return redirect(url_for('auth.view_store_products', store_id=str(store['_id'])))
    else:
        return redirect(url_for('auth.customer_dashboard'))


# ------------------ CATEGORY PRODUCTS --------------------
@auth_bp.route('/category/<category_name>')
def category_products(category_name):
    db = get_db()
    items = list(db.items.find({'category': category_name}))
    return render_template('auth/category_products.html', category=category_name, items=items)


# ------------------ CART --------------------
@auth_bp.route('/cart')
def view_cart():
    if 'customer' not in session:
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('auth.customer_login'))
    
    db = get_db()
    customer = db.customers.find_one({'_id': ObjectId(session['customer'])})
    if not customer:
        session.pop('customer', None)
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('auth.customer_login'))

    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    # Calculate and store initial grand total in session
    if total > 0:
        delivery_fee = 40
        taxes = total * 0.05
        grand_total = total + delivery_fee + taxes
        session['grand_total'] = grand_total
    
    return render_template('auth/cart.html', cart=cart, total=total, customer=customer)

@auth_bp.route('/api/category/<category_name>')
def api_category_products(category_name):
    db = get_db()

    # Normalize category name (lowercase)
    category_name = category_name.lower()

    # Use case-insensitive match
    query = {} if category_name == "all" else {
        'category': {'$regex': f"^{category_name}$", '$options': 'i'}
    }

    items = list(db.items.find(query))

    # Get store phone numbers from items
    store_phones = list(set(item.get('store_phone') for item in items if 'store_phone' in item))

    # Map phone → store name
    stores = db.stores.find({'phone': {'$in': store_phones}})
    phone_to_name = {store['phone']: store.get('store_name', 'Unknown Store') for store in stores}

    # Prepare response
    for item in items:
        item['_id'] = str(item['_id'])

        # Normalize photo field
        if 'photo' not in item:
            item['photo'] = item.get('image', '')  # fallback if only 'image' is present

        # Add store_owner field
        store_phone = item.get('store_phone')
        item['store_owner'] = phone_to_name.get(store_phone, 'Unknown Store')

    return jsonify(items)



@auth_bp.route('/api/update-cart-quantity', methods=['POST'])
def api_update_cart_quantity():
    if 'cart' not in session:
        return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')

    if not item_id or not isinstance(quantity, int) or quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid data.'}), 400

    for item in session['cart']:
        if item['id'] == item_id:
            item['quantity'] = quantity
            session.modified = True
            subtotal = item['price'] * quantity
            total = sum(i['price'] * i['quantity'] for i in session['cart'])
            return jsonify({'success': True, 'subtotal': subtotal, 'total': total})

    return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404

@auth_bp.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    if 'customer' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    data = request.get_json()
    item_id = data.get('item_id')
    if not item_id:
        return jsonify({'success': False, 'message': 'No item_id provided'}), 400

    db = get_db()
    product = db.items.find_one({"_id": ObjectId(item_id)})

    if not product:
        return jsonify({'success': False, 'message': 'Product not found!'}), 404

    if 'cart' not in session:
        session['cart'] = []

    found_in_cart = False
    for item in session['cart']:
        if item['id'] == item_id:
            item['quantity'] += 1
            found_in_cart = True
            break

    if not found_in_cart:
        session['cart'].append({
            'id': item_id,
            'name': product['name'],
            'price': float(product['price']),
            'quantity': 1
        })

    session.modified = True

    return jsonify({
        'success': True,
        'product_name': product['name'],
        'cart_count': len(session['cart'])
    })



@auth_bp.route('/add-addon-to-cart/<addon_id>')
def add_addon_to_cart(addon_id):
    """Adds an addon item to the cart."""
    db = get_db()
    addon = db.items.find_one({'_id': ObjectId(addon_id)})
    
    if not addon:
        flash('Addon not found.', 'danger')
        return redirect(url_for('auth.view_cart'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    session['cart'].append({
        'id': str(addon['_id']),
        'name': addon['name'],
        'price': float(addon['price']),
        'quantity': 1,
        'image': addon.get('image'),
        'description': addon.get('description', '')
    })
    session.modified = True
    
    flash(f'{addon["name"]} added to cart!', 'success')
    return redirect(url_for('auth.view_cart'))

@auth_bp.route('/api/remove_from_cart', methods=['POST'])
def api_remove_from_cart():
    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'message': 'No item_id provided'}), 400
    
    if 'cart' not in session or not isinstance(session['cart'], list):
        return jsonify({'success': False, 'message': 'Cart is empty or invalid'}), 400

    new_cart = [item for item in session['cart'] if item['id'] != item_id]
    session['cart'] = new_cart
    session.modified = True

    total = sum(item['price'] * item['quantity'] for item in new_cart)
    cart_length = len(new_cart)

    return jsonify({'success': True, 'total': total, 'cart_length': cart_length})


@auth_bp.route('/clear-cart')
def clear_cart():
    """Clears the entire cart."""
    session.pop('cart', None)
    flash('Cart cleared successfully.', 'success')
    return redirect(url_for('auth.view_cart'))

@auth_bp.route('/store/<store_id>')
def view_store_products(store_id):
    """Shows products for a specific store."""
    if 'customer' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.customer_login'))
    
    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(store_id)})
    if not store:
        flash('Store not found.', 'danger')
        return redirect(url_for('auth.customer_dashboard'))
    
    items = list(db.items.find({'store_phone': store['phone']}))
    
    return render_template('store_products.html', store=store, items=items)

@auth_bp.route('/update_cart', methods=['POST'])
def update_cart():
    """
    Update the entire cart quantities at once, based on form inputs like:
    quantities[item_id] = new_quantity
    """
    if 'cart' not in session:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('auth.view_cart'))
    
    quantities_dict = {}
    for key, value in request.form.items():
        if key.startswith('quantities[') and key.endswith(']'):
            item_id = key[10:-1]
            try:
                qty = int(value)
                if qty < 1:
                    qty = 1
            except ValueError:
                qty = 1
            quantities_dict[item_id] = qty

    cart = session['cart']
    for item in cart:
        item_id = item['id']
        if item_id in quantities_dict:
            item['quantity'] = quantities_dict[item_id]

    session['cart'] = cart
    session.modified = True
    flash('Cart updated successfully!', 'success')
    return redirect(url_for('auth.view_cart'))

# ------------------ GRAND TOTAL --------------------
@auth_bp.route('/api/set_grand_total', methods=['POST'])
def api_set_grand_total():
    data = request.get_json()
    session['grand_total'] = data.get('grand_total', 0)
    return jsonify(success=True)

# ------------------ PAYMENT GATEWAY --------------------
@auth_bp.route('/payment')
def payment_gateway():
    grand_total = session.get('grand_total', 0)
    return render_template('auth/payment.html', total_amount=grand_total)

@auth_bp.route('/place-order', methods=['POST'])
def place_order():
    if 'customer' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401

    db = get_db()
    customer = db.customers.find_one({'_id': ObjectId(session['customer'])})
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found'}), 404

    cart = session.get('cart', [])
    grand_total = session.get('grand_total', 0)

    if not cart:
        return jsonify({'success': False, 'message': 'Your cart is empty'}), 400

    order_items = []
    for item in cart:
        order_items.append({
            'product_id': ObjectId(item['id']),
            'name': item['name'],
            'quantity': item['quantity']
        })

    order = {
        'user_id': customer['_id'],
        'name': customer['name'],
        'address': customer['address'],
        'items': order_items,
        'total_amount': grand_total,
        'payment_method': request.form.get('method'),
        'placed_at': datetime.now()
    }

    result = db.orders.insert_one(order)

    # Clear cart after order
    session.pop('cart', None)

    item_summary = ", ".join([f"{i['name']} × {i['quantity']}" for i in order_items])
    return jsonify({
        'success': True,
        'order_id': str(result.inserted_id),
        'name': customer['name'],
        'address': f"{customer['address']['flat_no']}, {customer['address']['street']}, {customer['address']['landmark']}, {customer['address']['city']} - {customer['address']['pincode']}",
        'items': item_summary
    })


@auth_bp.route('/customer/logout')
def customer_logout():
    """Logs out the customer and clears their session."""
    session.pop('customer', None)
    session.pop('cart', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.customer_login'))



# ------------------ STORE --------------------
@auth_bp.route('/store/register', methods=['GET', 'POST'])
def store_register():
    """Handles store registration."""
    db = get_db()
    if request.method == 'POST':
        if db.stores.find_one({'phone': request.form['phone']}):
            flash('A store with this phone number already exists.', 'danger')
            return redirect(url_for('auth.store_register'))
        if db.stores.find_one({'email': request.form['email']}):
            flash('A store with this email already exists.', 'danger')
            return redirect(url_for('auth.store_register'))

        # Storing password directly in plain text (NOT RECOMMENDED for security)
        data = {
            "store_name": request.form['store_name'],
            "owner_name": request.form['owner_name'],
            "phone": request.form['phone'],
            "email": request.form['email'],
            "password": request.form['password'], # Plain text password
            "address": {
                "flat_no": request.form['flat_no'],
                "street": request.form['street'],
                "landmark": request.form['landmark'],
                "city": request.form['city'],
                "state": request.form['state'],
                "pincode": request.form['pincode']
            }
        }
        db.stores.insert_one(data)
        flash('Store registration successful! Please log in.', 'success')
        return redirect(url_for('auth.store_login'))
    return render_template('auth/store_register.html')

@auth_bp.route('/store/login', methods=['GET', 'POST'])
def store_login():
    """Handles store login."""
    db = get_db()
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        # Plain text password check
        store = db.stores.find_one({'phone': phone, 'password': password})
        if store:
            session['store'] = str(store['_id'])
            flash('Logged in successfully!', 'success')
            return redirect(url_for('auth.store_dashboard'))
        else:
            flash("Invalid phone number or password. Please try again.", 'danger')
    return render_template('auth/store_login.html')

@auth_bp.route('/store/dashboard')
def store_dashboard():
    """Displays the store dashboard with their items and sales report."""
    if 'store' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(session['store'])})
    if not store:
        session.pop('store', None)
        flash('Your session is invalid. Please log in again.', 'danger')
        return redirect(url_for('auth.store_login'))

    items = list(db.items.find({'store_phone': store['phone']}))

    seven_days_ago = datetime.now() - timedelta(days=7)
    pipeline = [
        {"$match": {
            "store_phone": store['phone'],
            "order_date": {"$gte": seven_days_ago}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$order_date"}},
            "total_sales": {"$sum": "$total_amount"}
        }},
        {"$sort": SON([("_id", -1)])}
    ]
    sales_data = list(db.orders.aggregate(pipeline))
    sales_report = [{"date": s["_id"], "total_sales": s["total_sales"]} for s in sales_data]

    return render_template('store_dashboard.html', store=store, items=items, sales_report=sales_report)

@auth_bp.route('/store/profile')
def store_profile():
    """Displays the store's profile."""
    if 'store' not in session:
        flash('Please log in to access your profile.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({"_id": ObjectId(session['store'])})

    if store:
        return render_template("store_profile.html", store=store)
    else:
        session.pop('store', None)
        flash("Store not found or session invalid. Please log in again.", "danger")
        return redirect(url_for('auth.store_login'))

@auth_bp.route('/store/add-item', methods=['POST'])
def add_item():
    """Handles adding a new item by a store."""
    if 'store' not in session:
        flash('Please log in to add items.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(session['store'])})
    if not store:
        session.pop('store', None)
        flash('Invalid session. Please log in again.', 'danger')
        return redirect(url_for('auth.store_login'))

    image_file = request.files.get('image')
    image_data = None
    if image_file and image_file.filename != '':
        if not image_file.content_type.startswith('image/'):
            flash('Uploaded file is not an image.', 'danger')
            return redirect(url_for('auth.store_dashboard'))
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Get the selected category from the form
    category = request.form.get('category')
    if category not in ['Pizza', 'Beverage','Breads']:
        flash('Please select a valid category.', 'danger')
        return redirect(url_for('auth.store_dashboard'))

    item = {
        "store_owner": store['owner_name'],
        "name": request.form['name'],
        "price": float(request.form['price']),
        "description": request.form['description'],
        "category": category,  # <-- Add category here
        "store_phone": store['phone'],
        "image": image_data
    }

    db.items.insert_one(item)
    flash('Product added successfully!', 'success')
    return redirect(url_for('auth.store_dashboard'))


@auth_bp.route('/store/delete-item/<item_id>')
def delete_item(item_id):
    """Deletes an item belonging to the logged-in store."""
    if 'store' not in session:
        flash('Please log in to delete items.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(session['store'])})
    if not store:
        session.pop('store', None)
        flash('Invalid session. Please log in again.', 'danger')
        return redirect(url_for('auth.store_login'))

    result = db.items.delete_one({'_id': ObjectId(item_id), 'store_phone': store['phone']})
    if result.deleted_count == 1:
        flash('Item deleted successfully!', 'success')
    else:
        flash('Item not found or you are not authorized to delete it.', 'danger')
    return redirect(url_for('auth.store_dashboard'))

@auth_bp.route('/store/edit-item/<item_id>', methods=['GET'])
def edit_item_form(item_id):
    """Displays the form to edit an item."""
    if 'store' not in session:
        flash('Please log in to edit items.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(session['store'])})
    if not store:
        session.pop('store', None)
        flash('Invalid session. Please log in again.', 'danger')
        return redirect(url_for('auth.store_login'))

    item = db.items.find_one({'_id': ObjectId(item_id), 'store_phone': store['phone']})
    if not item:
        flash("Item not found or unauthorized.", 'danger')
        return redirect(url_for('auth.store_dashboard'))

    return render_template('edit_item.html', item=item)

@auth_bp.route('/store/edit-item/<item_id>', methods=['POST'])
def edit_item_submit(item_id):
    """Handles the submission of the item edit form."""
    if 'store' not in session:
        flash('Please log in to edit items.', 'warning')
        return redirect(url_for('auth.store_login'))

    db = get_db()
    store = db.stores.find_one({'_id': ObjectId(session['store'])})
    if not store:
        session.pop('store', None)
        flash('Invalid session. Please log in again.', 'danger')
        return redirect(url_for('auth.store_login'))

    item = db.items.find_one({'_id': ObjectId(item_id), 'store_phone': store['phone']})
    if not item:
        flash("Item not found or you are not authorized to edit it.", 'danger')
        return redirect(url_for('auth.store_dashboard'))

    update_data = {
        'name': request.form['name'],
        'price': float(request.form['price']),
        'description': request.form['description']
    }

    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        if not image_file.content_type.startswith('image/'):
            flash('Uploaded file is not an image.', 'danger')
            return redirect(url_for('auth.store_dashboard'))
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        update_data['image'] = image_data
    elif request.form.get('clear_image') == 'on':
        update_data['image'] = None

    db.items.update_one(
        {'_id': ObjectId(item_id), 'store_phone': store['phone']},
        {'$set': update_data}
    )
    flash('Item updated successfully!', 'success')
    return redirect(url_for('auth.store_dashboard'))


@auth_bp.route('/store/logout')
def store_logout():
    """Logs out the store and clears their session."""
    session.pop('store', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.store_login'))