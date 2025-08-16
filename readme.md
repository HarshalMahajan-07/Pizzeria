
# 🍕 Pizzeria a pizza-ordering-system

Pizzeria is a full-stack food ordering web application built to deliver a smooth and intuitive experience for both customers and pizza store owners. Whether you're hungry for a cheesy slice or managing a local pizzeria, this system has you covered.

Designed with a modern interface and powered by Flask and MongoDB, the platform enables real-time ordering, secure authentication, and seamless management of menus, orders, and user profiles. Customers can explore pizza categories, build their cart, and place orders — all from an elegant dashboard inspired by popular food delivery services. Meanwhile, store owners get a powerful backend to manage their inventory, view customer orders, and maintain their store profile with ease.

Perfect for educational use, startups, or anyone looking to build a robust food delivery system, this project combines clean code architecture, responsive design, and functional simplicity into one delicious package.


## 🚀 Features

### 👤 Customer
- Register/Login with phone number, email, password, and address
- Browse pizza categories and items
- Add pizzas to cart
- Place orders with payment simulation
- View and manage their profile
- Track order status

### 🏪 Store
- Register/Login with store details and owner credentials
- Add, edit, and delete pizza items
- View all orders placed by customers
- Manage store profile and offerings

## 🧰 Tech Stack

- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Backend:** Python (Flask)
- **Database:** MongoDB
- **Templating:** Jinja2
- **Authentication:** Custom session-based system

## 📁 Project Structure

```

pizza-ordering-system/
│
├── app.py                         # Main Flask app
├── requirements.txt              # Python dependencies
│
├── models/
│   └── db.py                     # MongoDB connection setup
│
├── routes/
│   └── auth\_routes.py            # All route handlers
│
├── templates/
│   ├── customer\_dashboard.html
│   ├── store\_dashboard.html
│   ├── auth/                     # Authentication templates
│   │   ├── customer\_login.html
│   │   ├── customer\_register.html
│   │   ├── store\_login.html
│   │   └── store\_register.html
│   ├── cart.html, my\_orders.html, etc.
│
└── static/                       # Assets (CSS/JS/Images)

````
## Screenshots


<img width="1896" height="864" alt="Screenshot 2025-08-03 162139" src="https://github.com/user-attachments/assets/4fb81851-3781-4bf6-a3b7-d3980f84b105" />

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/pizza-ordering-system.git
   cd pizza-ordering-system
````

2. **Install dependencies**

   ```bash/cmd
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash/cmd
   python app.py
   ```

4. **Visit**

   ```browser
   http://127.0.0.1:5000
   ```


## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

> Made with ❤️ for food tech experimentation!

```
