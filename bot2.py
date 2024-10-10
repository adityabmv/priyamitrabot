import discord
from discord.ext import commands
from discord import ui, app_commands
from datetime import datetime
from typing import List



import discord
import json
from discord import app_commands
from discord.ext import commands
from pathlib import Path

TOKEN = "MTI5MzI0ODgwNjc4NzM1MDY2MA.G9jjFV.lWd2LS8UO3858Nys2Ec7SuT5V5xX3jln6THcXY"

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())



class Task:
    def __init__(self, task_name, description, deadline=None):
        self.task_name = task_name
        self.description = description
        self.assignees = []
        self.deadline = deadline
        self.completed = False

    def assign(self, user):
        if user not in self.assignees:
            self.assignees.append(user)

    def unassign(self, user):
        if user in self.assignees:
            self.assignees.remove(user)

    def set_deadline(self, deadline):
        self.deadline = deadline

    def complete(self):
        self.completed = True

    def update_progress(self, completed: bool):
        self.completed = completed

    def status(self):
        if self.completed:
            return "Completed"
        elif self.deadline and datetime.now() > self.deadline:
            return "Pending (Overdue)"
        elif self.deadline and datetime.now() < self.deadline:
            return "Pending (In Progress)"
        else:
            return "Not Started"


class Project:
    def __init__(self, name):
        self.name = name
        self.tasks = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def remove_task(self, task_name):
        self.tasks = [task for task in self.tasks if task.task_name != task_name]

    def get_tasks(self, status=None):
        if status:
            return [task for task in self.tasks if task.status() == status]
        return self.tasks

    def edit_task(self, old_task_name, new_task_name=None, description=None, deadline=None):
        for task in self.tasks:
            if task.task_name == old_task_name:
                if new_task_name:
                    task.task_name = new_task_name
                if description:
                    task.description = description
                if deadline:
                    task.set_deadline(deadline)
                return True
        return False


class TaskManager:
    def __init__(self):
        self.projects = []

    def create_project(self, project_name):
        project = Project(project_name)
        self.projects.append(project)

    def get_project(self, project_name):
        for project in self.projects:
            if project.name == project_name:
                return project
        return None

    def get_all_projects(self):
        return self.projects

    def delete_project(self, project_name):
        self.projects = [project for project in self.projects if project.name != project_name]

    def summary(self):
        summary_str = "**Project Summary**:\n\n"
        for project in self.projects:
            summary_str += f"📂 **Project**: {project.name}\n"
            for task in project.tasks:
                assignees = ', '.join([assignee.display_name for assignee in task.assignees])
                summary_str += f"  - **Task**: {task.task_name}\n    **Status**: {task.status()}\n    **Assignees**: {assignees or 'None'}\n"
            summary_str += "\n"
        return summary_str if self.projects else "No projects found."


# Initialize Task Manager
task_manager = TaskManager()


# Helper function to format task details
def format_task(task: Task):
    assignees = ', '.join([assignee.display_name for assignee in task.assignees])
    return f"**Task**: {task.task_name}\n**Description**: {task.description}\n**Assignees**: {assignees or 'None'}\n**Deadline**: {task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else 'No deadline'}\n**Status**: {task.status()}"


# View Projects (select menu)
class ProjectSelect(ui.Select):
    def __init__(self, projects: List[Project]):
        options = [discord.SelectOption(label=project.name, description="Select a project") for project in projects]
        super().__init__(placeholder="Choose a project", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        project_name = self.values[0]
        project = task_manager.get_project(project_name)
        tasks = "\n\n".join([format_task(task) for task in project.get_tasks()])
        await interaction.response.send_message(f"**Project: {project.name}**\n\n{tasks or 'No tasks in this project.'}", ephemeral=True)


class TaskSelect(ui.Select):
    def __init__(self, tasks: List[Task]):
        options = [discord.SelectOption(label=task.task_name, description="Select a task") for task in tasks]
        super().__init__(placeholder="Choose a task", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        task_name = self.values[0]
        project = next((p for p in task_manager.projects if task_name in [t.task_name for t in p.tasks]), None)
        task = next((t for t in project.tasks if t.task_name == task_name), None)
        await interaction.response.send_message(f"**Task Details**\n\n{format_task(task)}", ephemeral=True)


# Command: /create_project
@bot.tree.command(name="create_project", description="Create a new project")
async def create_project(interaction: discord.Interaction, name: str):
    task_manager.create_project(name)
    await interaction.response.send_message(f"✅ Project '{name}' created.", ephemeral=True)


# Command: /create_task
@bot.tree.command(name="create_task", description="Create a new task in a project")
async def create_task(interaction: discord.Interaction, project_name: str, task_name: str, description: str):
    project = task_manager.get_project(project_name)
    if project:
        task = Task(task_name, description)
        project.add_task(task)
        await interaction.response.send_message(f"✅ Task '{task_name}' created in project '{project_name}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Project '{project_name}' not found.", ephemeral=True)


# Command: /assign_task
@bot.tree.command(name="assign_task", description="Assign a task to a user")
async def assign_task(interaction: discord.Interaction, task_name: str, member: discord.Member):
    project = next((p for p in task_manager.projects if task_name in [t.task_name for t in p.tasks]), None)
    task = next((t for t in project.tasks if t.task_name == task_name), None)
    if task:
        task.assign(member)
        await interaction.response.send_message(f"✅ {member.display_name} assigned to task '{task_name}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Task '{task_name}' not found.", ephemeral=True)


# Command: /unassign_task
@bot.tree.command(name="unassign_task", description="Unassign a user from a task")
async def unassign_task(interaction: discord.Interaction, task_name: str, member: discord.Member):
    project = next((p for p in task_manager.projects if task_name in [t.task_name for t in p.tasks]), None)
    task = next((t for t in project.tasks if t.task_name == task_name), None)
    if task:
        task.unassign(member)
        await interaction.response.send_message(f"✅ {member.display_name} unassigned from task '{task_name}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Task '{task_name}' not found.", ephemeral=True)


# Command: /set_deadline
@bot.tree.command(name="set_deadline", description="Set a deadline for a task")
async def set_deadline(interaction: discord.Interaction, task_name: str, deadline: str):
    project = next((p for p in task_manager.projects if task_name in [t.task_name for t in p.tasks]), None)
    task = next((t for t in project.tasks if t.task_name == task_name), None)
    if task:
        deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        task.set_deadline(deadline_dt)
        await interaction.response.send_message(f"✅ Deadline for task '{task_name}' set to {deadline}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Task '{task_name}' not found.", ephemeral=True)


# Command: /complete_task
@bot.tree.command(name="complete_task", description="Mark a task as complete")
async def complete_task(interaction: discord.Interaction, task_name: str):
    project = next((p for p in task_manager.projects if task_name in [t.task_name for t in p.tasks]), None)
    task = next((t for t in project.tasks if t.task_name == task_name), None)
    if task:
        task.complete()
        await interaction.response.send_message(f"✅ Task '{task_name}' marked as complete.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Task '{task_name}' not found.", ephemeral=True)


# Command: /delete_task
@bot.tree.command(name="delete_task", description="Delete a task")
async def delete_task(interaction: discord.Interaction, project_name: str, task_name: str):
    project = task_manager.get_project(project_name)
    if project:
        project.remove_task(task_name)
        await interaction.response.send_message(f"✅ Task '{task_name}' deleted from project '{project_name}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Project '{project_name}' not found.", ephemeral=True)


# Command: /project_summary
@bot.tree.command(name="project_summary", description="Get a summary of a project")
async def project_summary(interaction: discord.Interaction, project_name: str):
    project = task_manager.get_project(project_name)
    if project:
        tasks = "\n\n".join([format_task(task) for task in project.get_tasks()])
        await interaction.response.send_message(f"**Project: {project.name}**\n\n{tasks or 'No tasks in this project.'}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Project '{project_name}' not found.", ephemeral=True)


# Command: /summary
@bot.tree.command(name="summary", description="Get a summary of all projects and tasks")
async def summary(interaction: discord.Interaction):
    summary_text = task_manager.summary()
    await interaction.response.send_message(summary_text, ephemeral=True)







# Path to JSON file
data_file = Path("user_status.json")

# Function to load or initialize the JSON file
def load_data():
    if not data_file.exists():
        return {"in": [], "out": []}
    with open(data_file, "r") as f:
        return json.load(f)

# Function to save data to the JSON file
def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

# Function to generate a status message with nicknames
def generate_status_message(data, guild):
    in_users = ", ".join([guild.get_member(user_id).display_name for user_id in data['in'] if guild.get_member(user_id)]) or "No users are currently marked as 'In Work'."
    out_users = ", ".join([guild.get_member(user_id).display_name for user_id in data['out'] if guild.get_member(user_id)]) or "No users are currently marked as 'Out of Work'."
    return (
        f"**Current Status Update**\n\n"
        f"📂 **In Work**:\n{in_users}\n\n"
        f"🗃️ **Out of Work**:\n{out_users}"
    )

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# /in command
@bot.tree.command(name='in', description='Mark yourself as "In Work"')
async def in_work(interaction: discord.Interaction):
    data = load_data()
    user_id = interaction.user.id
    
    # Remove user from 'out' list if they are there
    if user_id in data['out']:
        data['out'].remove(user_id)
    
    # Add user to 'in' list if they are not already there
    if user_id not in data['in']:
        data['in'].append(user_id)
    
    save_data(data)
    
    status_message = generate_status_message(data, interaction.guild)
    
    # Send ephemeral message to the user
    await interaction.response.send_message(f"✅ Your status has been updated: **You are marked as 'In Work'.**", ephemeral=True)
    
    # Send updated status message to the channel
    await interaction.channel.send(embed=discord.Embed(
        title="Status Update",
        description=status_message,
        color=discord.Color.green()
    ))

# /out command
@bot.tree.command(name='out', description='Mark yourself as "Out of Work"')
async def out_work(interaction: discord.Interaction):
    data = load_data()
    user_id = interaction.user.id
    
    # Remove user from 'in' list if they are there
    if user_id in data['in']:
        data['in'].remove(user_id)
    
    # Add user to 'out' list if they are not already there
    if user_id not in data['out']:
        data['out'].append(user_id)
    
    save_data(data)
    
    status_message = generate_status_message(data, interaction.guild)
    
    # Send ephemeral message to the user
    await interaction.response.send_message(f"✅ Your status has been updated: **You are marked as 'Out of Work'.**", ephemeral=True)
    
    # Send updated status message to the channel
    await interaction.channel.send(embed=discord.Embed(
        title="Status Update",
        description=status_message,
        color=discord.Color.red()
    ))

# /io command to show how many users are "in" and "out"
@bot.tree.command(name='io', description='Show how many users are currently "In Work" and "Out of Work"')
async def io_status(interaction: discord.Interaction):
    data = load_data()
    
    in_count = len(data['in'])
    out_count = len(data['out'])
    
    # Send ephemeral message to the user showing counts
    await interaction.response.send_message(
        f"📊 **Current Status Overview**\n\n"
        f"**In Work**: {in_count} users\n"
        f"**Out of Work**: {out_count} users", 
        ephemeral=True
    )

bot.run(TOKEN)





