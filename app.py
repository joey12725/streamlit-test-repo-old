import streamlit as st
from datetime import datetime, timedelta
import os
import pickle
from typing import List
import random
from streamlit_tags import st_tags

# Define the classes from the previous step
class User:
    def __init__(self, username: str, password: str, role: str):
        self.username = username
        self.password = password
        self.role = role
        self.partner = None

    def link_partner(self, partner):
        if self.partner is None:
            self.partner = partner
            partner.partner = self
            return True
        return False

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "partner": self.partner.username if self.partner else None
        }

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

class Dom(User):
    def __init__(self, username: str, password: str):
        super().__init__(username, password, "Dom")
        self.tasks = []

    def assign_task(self, sub, task):
        if isinstance(sub, Sub) and self.partner == sub:
            sub.tasks.append(task)

    def delete_task(self, sub, task):
        if isinstance(sub, Sub) and self.partner == sub:
            sub.tasks = [t for t in sub.tasks if t != task]

    def assign_reward(self, sub, points, reward):
        if isinstance(sub, Sub) and self.partner == sub:
            sub.rewards.append((points, reward))

    def assign_punishment(self, sub, points, punishment):
        if isinstance(sub, Sub) and self.partner == sub:
            sub.punishments.append((points, punishment))

class Sub(User):
    def __init__(self, username: str, password: str):
        super().__init__(username, password, "Sub")
        self.tasks = []
        self.rewards = []
        self.punishments = []
        self.points = 0

    def complete_task(self, task):
        for t in self.tasks:
            if t == task:
                t.completed = True
                self.points += t.points
                return t.points

    def submit_proof(self, task, proof):
        if task.require_proof:
            proof_path = f"proofs/{self.username}/{task.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            os.makedirs(os.path.dirname(proof_path), exist_ok=True)
            with open(proof_path, 'wb') as f:
                f.write(proof)
            return proof_path

    def check_rewards_and_punishments(self):
        today = datetime.now().date()  # Ensure `today` is a date object
        earned_rewards = []
        received_punishments = []
        
        for points, reward in self.rewards:
            if self.points >= points:
                earned_rewards.append(reward)
        
        for points, punishment in self.punishments:
            # Ensure `punishment.due_date` is compared as a date
            if self.points < points and today > punishment.due_date.date():
                received_punishments.append(punishment)
        
        return earned_rewards, received_punishments
class Task:
    def __init__(self, name: str, points: int, rewards: list, punishments: list, due_date: datetime, require_proof: bool):
        self.name = name
        self.points = points
        self.rewards = rewards
        self.punishments = punishments
        self.due_date = due_date
        self.require_proof = require_proof
        self.completed = False
        self.proof_path = None

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "name": self.name,
            "points": self.points,
            "rewards": self.rewards,
            "punishments": self.punishments,
            "due_date": self.due_date.isoformat(),
            "require_proof": self.require_proof,
            "completed": self.completed,
            "proof_path": self.proof_path
        }

# Load or create user data
def load_users():
    if os.path.exists('users.pkl'):
        with open('users.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        return {}

def save_users(users):
    with open('users.pkl', 'wb') as f:
        pickle.dump(users, f)

# Initialize users dictionary
users = load_users()

# Streamlit app configuration
st.set_page_config(page_title="TNG Obedience Tracker", page_icon="😈")

# Function to handle user session
def get_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
    return st.session_state

# Initialize session state
session_state = get_session_state()

# App title and tagline
st.title('TNG Obedience Tracker 😈')
st.subheader('Casual sex, Competitive Kink')

# Sidebar menu
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

# Function to display tasks
def display_tasks(user):
    st.subheader("Tasks")
    if user.tasks:
        for task in user.tasks:
            with st.expander(f"Task: {task.name}"):
                st.text(str(task))

                if not task.completed:
                    if st.button(f"Complete Task - {task.name}"):
                        user.complete_task(task)
                        save_users(users)  # Ensure state is saved after completing the task
                        st.success(f"Task {task.name} Completed")

                    if task.require_proof:
                        proof = st.file_uploader(f"Upload Proof for {task.name}")
                        if proof and st.button(f"Submit Proof - {task.name}"):
                            task.proof_path = user.submit_proof(task, proof.read())
                            save_users(users)  # Ensure state is saved after submitting proof
                            st.success(f"Proof for {task.name} Submitted")
                else:
                    st.write("Task Completed")
                    if task.proof_path:
                        st.image(task.proof_path, caption=f"Proof for {task.name}")


# Function to display rewards and punishments
def display_rewards_punishments(user):
    st.subheader("Current Points")
    st.write(f"Points: {user.points}")

    st.subheader("Earned Rewards and Punishments")
    rewards, punishments = user.check_rewards_and_punishments()
    if rewards:
        st.write("**Rewards:**")
        for reward in rewards:
            st.write(f"- {reward}")
    if punishments:
        st.write("**Punishments:**")
        for punishment in punishments:
            st.write(f"- {punishment}")

    st.subheader("Potential Rewards and Punishments")
    if user.rewards:
        st.write("**Rewards:**")
        for points, reward in user.rewards:
            if reward not in rewards:
                st.write(f"more than {points} points: {reward}")
    if user.punishments:
        st.write("**Punishments:**")
        for points, punishment in user.punishments:
            st.write(f"less than {points} points: {punishment}")

# Function to display completed tasks with proofs for Doms
def display_completed_tasks_with_proofs(dom):
    st.subheader("Completed Tasks with Proofs")
    if dom.partner.tasks:
        for task in dom.partner.tasks:
            if task.completed:
                with st.expander(f"Task: {task.name}"):
                    st.text(str(task))
                    if task.proof_path:
                        st.image(task.proof_path, caption=f"Proof for {task.name}")


# Account creation
if choice == "Sign Up":
    st.subheader("Create New Account")

    username = st.text_input("User Name", key="signup_username")
    password = st.text_input("Password", type='password', key="signup_password")
    role = st.selectbox("Role", ["Dom", "Sub"], key="signup_role")

    if st.button("Sign Up"):
        if username in users:
            st.warning("Username already exists")
        else:
            if role == "Dom":
                new_user = Dom(username, password)
            else:
                new_user = Sub(username, password)
            users[username] = new_user
            save_users(users)
            st.success("You have successfully created an account")
            st.info("Go to Login Menu to login")

# User login
elif choice == "Login":
    st.subheader("Login")

    username = st.text_input("User Name")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if username in users and users[username].password == password:
            st.success(f"Welcome {username}")
            session_state['logged_in'] = True
            session_state['username'] = username
        else:
            st.warning("Incorrect Username/Password")

# Main app functionality for logged-in users
if session_state['logged_in']:
    user = users[session_state['username']]

    if user.partner:
        st.info(f"Linked with: {user.partner.username}")

        if user.role == "Dom":
            st.subheader("Assign Task")
            task_name = st.text_input("Task Name")
            task_points = st.number_input("Task Points", min_value=0)
            task_rewards = st_tags(label='Task Rewards', text='Press enter to add more')
            task_punishments = st_tags(label='Task Punishments', text='Press enter to add more')
            task_due_date = st.date_input("Due Date")
            task_require_proof = st.checkbox("Require Proof")

            if st.button("Assign Task"):
                task = Task(
                    name=task_name,
                    points=task_points,
                    rewards=task_rewards,
                    punishments=task_punishments,
                    due_date=datetime.combine(task_due_date, datetime.min.time()),
                    require_proof=task_require_proof
                )
                user.assign_task(user.partner, task)
                save_users(users)
                st.success("Task Assigned")

            st.subheader("Sub's Tasks")
            if user.partner.tasks:
                for task in user.partner.tasks:
                    with st.expander(f"Task: {task.name}"):
                        st.write(f"**Points**: {task.points}")
                        st.write(f"**Due Date**: {task.due_date}")
                        st.write(f"**Rewards**: {', '.join(task.rewards)}")
                        st.write(f"**Punishments**: {', '.join(task.punishments)}")
                        st.write(f"**Require Proof**: {'Yes' if task.require_proof else 'No'}")

                        if task.proof_path:
                            st.image(task.proof_path, caption=f"Proof for {task.name}")
                        else:
                            st.write("Proof not uploaded yet.")

            st.subheader("Sub's Points")
            st.write(f"Points: {user.partner.points}")

            st.subheader("Assign Rewards and Punishments")
            reward_points = st.number_input("Points to Reward", min_value=0, key="reward_points")
            reward_description = st.text_input("Reward Description", key="reward_description")
            if st.button("Assign Reward"):
                user.assign_reward(user.partner, reward_points, reward_description)
                save_users(users)
                st.success("Reward Assigned")

            punishment_points = st.number_input("Points to Punish", min_value=0, key="punishment_points")
            punishment_description = st.text_input("Punishment Description", key="punishment_description")
            punishment_due_date = st.date_input("Punishment Due Date", key="punishment_due_date")
            if st.button("Assign Punishment"):
                punishment = Task(
                    name=punishment_description,
                    points=punishment_points,
                    rewards=[],
                    punishments=[],
                    due_date=datetime.combine(punishment_due_date, datetime.min.time()),
                    require_proof=False
                )
                user.assign_punishment(user.partner, punishment_points, punishment)
                save_users(users)
                st.success("Punishment Assigned")

            display_completed_tasks_with_proofs(user)

        elif user.role == "Sub":
            display_tasks(user)
            display_rewards_punishments(user)

    else:
        partner_username = st.text_input("Link with partner (enter username)")
        if st.button("Link"):
            if partner_username in users and users[partner_username].role != user.role:
                if user.link_partner(users[partner_username]):
                    save_users(users)
                    st.success(f"Linked with {partner_username}")
                else:
                    st.warning("Already linked")
            else:
                st.warning("Invalid partner username or same role")

# Save updated users data
save_users(users)

# Handle user logout
if st.sidebar.button("Logout"):
    session_state['logged_in'] = False
    session_state['username'] = None
    st.success("Successfully logged out")

# Redirect to login page if not logged in
if not session_state['logged_in'] and choice != "Sign Up":
    st.warning("Please log in to access your account.")
