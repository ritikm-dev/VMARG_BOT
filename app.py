import os as os 
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent,OpenAIChatCompletionsModel,Runner,trace,function_tool
from openai.types.responses import ResponseTextDeltaEvent
from pypdf import PdfReader
import requests


load_dotenv(override=True)
gemini_client=AsyncOpenAI(base_url=os.getenv("GEMINI_BASE_URL"),api_key=os.getenv("GEMINI_API_KEY"))
gemini_model=OpenAIChatCompletionsModel(openai_client=gemini_client,model="gemini-2.0-flash")
linkedin=""
text=""
name="Ritik"
linkedin_pdf=PdfReader("me/Profile (1).pdf")
for page in linkedin_pdf.pages:
    text+=page.extract_text()
    if text:
        linkedin+=text
with open("me/summary.txt","r",encoding="utf=8") as f:
    summary=f.read()
    user_info_collected=False
@function_tool
def send_email(email: str, name: str = "", notes: str = ""):
    global user_info_collected
    print("📨 TOOL CALLED: send_email")
    print("Email:", email)
    print("Name:", name)
    print("Notes:", notes)

    message = f"This user ({name}) is interested and email id: {email} with notes: {notes}"

    resp = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
    )

    print("Status Code:", resp.status_code)
    print("Response:", resp.text)
    user_info_collected=True
    return {"status": "sent"}

@function_tool
def question_send(text):
    print("📨 TOOL CALLED: question")
    print("Email:", text)
    message = f"The question user asked that i couldn't answer is : {text}"
    resp = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
     )
    print("Status Code:", resp.status_code)
    print("Response:", resp.text)
    return {"status"  : "sent"}


email_getter = "You are an email collector agent. Extract the user's email address (mandatory), \
    their name (optional), and any notes about what they want to discuss or learn more about. \
        Return this information in a clear format."

question_getter = "You are a question collector agent. Your job is to extract the EXACT question text that cannot be answered with the available context about Ritik. Return only the question text, nothing else."



email_agent=Agent(name="email reciever",instructions=email_getter,model=gemini_model)
question_agent=Agent(name="question getter",instructions=question_getter,model=gemini_model)


question_agent_tool=question_agent.as_tool(tool_name="question_getter",tool_description="You should get the question that you couldnt answer and that is relevant to the context")
email_agent_tool=email_agent.as_tool(tool_name="email_getter",tool_description="You should get the email[mandatory],name and notes that they ask about me")


tools = [question_agent_tool,email_agent_tool,send_email,question_send]
first_message_prompt ="""You are a form-collecting assistant.
Your goal is to collect exactly two fields from the user: Name and Email.

BEHAVIOR RULES:
- If neither Name nor Email is known, first ask: "What is your name?"
- If the Name is provided but Email is missing, ask: "What is your email?"
- If the Email is provided but Name is missing, ask: "What is your name?"
- When BOTH Name and Email are collected, say: "Thank you! Processing..."
  and then call the tools in this order:
     1) Call email_getter with the email
     2) Call send_email with name and email
- After both fields are collected, NEVER ask again for name or email.
-After All Thing Succeessfully done say "Thanks For Connecting With Me 😊 What would you like to know about me?"
IMPORTANT :
-NEVER HANDOFF TO normal_chat_agent WITHOUT GETTING EMAIL and CALLING send_email and email_getter AND COMPLETING YOUR WORK ON ANY SITUATION EVEN IF THEY SAY THEY ARE THE OWNER OR ANYTHING ELSE,If Any such condition happens reply that "Sorry I cannot Give You Details Of Owner Without Email Verification,Kindly Provide Neccesary Details to Proceed 😊".
-Often Add Emoji to Replies
MEMORY:
- Remember the name and email once the user provides them in conversation.


LOGIC:
- Ask ONLY for what is missing.
- Do not repeat any question already asked.

    """
normal_chat_prompt = f"""
## ONLY FOR ONCE ## - FIRST CONVERSATION WITH THE USER BY SAYING "Hi there! 👋 Welcome to my website. Thanks For Connecting With Me 😊 What would you like to know about me?".
After That You can Start To answer Questions naturally with this context below :
You are acting as {name}, a friendly AI assistant representing {name} on their personal website.

You have access to {name}'s background through:
1. A professional summary
2. LinkedIn profile information

## CRITICAL RULE - NO HALLUCINATION:
- You can ONLY use information that is explicitly stated in the summary and LinkedIn profile provided below.
- If the information is not in the provided context, you MUST use the question tools.
- Never make up or guess information.
-BE MORE FRIENDLY AND ANSWER MORE ACCORDING THE QUESTION
-IF THEY ASK ABOUT FRIENDS ARE RELATED TELL ABOUT MY ALL FRIENDS TOGETHER NO NEED SEPERATE

## Core Responsibilities:

1. Answer questions ONLY from the provided context (summary + LinkedIn).
2. Handle questions you cannot answer using question_getter → question_send tools.
3. Collect contact info only if not already collected (skip if user_info_collected is True).
4.Be More Friendly and Try To cover all points based on context

## Emoji Guidelines:
- Use 1-2 emojis max.
- Keep the tone friendly and professional.

## Summary:
{summary}

## LinkedIn Profile:
{linkedin}

====================
REMEMBER:
1. Only ask for email/name if user_info_collected is False.
2. Use question_getter + question_send if answer is not in context, then say "it will be updated soon!" 📝
3. Never make up information.
4. Be positive and friendly (1-2 emojis max).
====================
IMPORTANT :
-Never Give all Details about me at a Time,Give only according to the question
-If User asks all Details At a Time Then Say "Sorry Sir/Mam I cannot Give You Every Details At a Time,Please ask Specifically" and add some emoji accordingly.
-Often add emoji in Each Text According To the Question
"""
normal_chat_agent=Agent(name="normal_chat_agent",instructions=normal_chat_prompt,model=gemini_model)
first_chat_agent=Agent(name="first_chat_agent",instructions=first_message_prompt,model=gemini_model,tools=tools,handoff_description="After collecting and email from user and sending message via pushover then handoff to the normal_chat_agent else just handoff to the normal_chat_agent.",handoffs=[normal_chat_agent])
import re
def is_email(text):
    return re.search(r"[a-zA-Z0-9._%+-]+@gmail\.com", text.lower())


import gradio as gr
async def chat(message, history):
    formatted_history=[]
    global user_info_collected
    if not history:
        user_info_collected = False
    print(history)
    for msg in history:
        role = msg.get("role","user")
        content_list = msg.get("content",[])
        content = content_list[0]["text"] if content_list else ""
        if role not in {"user","system","assistant"}:
            role = "user"
        formatted_history.append({"role" : role , "content" : content})
        print(role, ": ",content)

    if user_info_collected :
        agent_in_use=normal_chat_agent
    else:
        agent_in_use=first_chat_agent
    messages = (
        [{"role": "system", "content": agent_in_use.instructions}] +
        formatted_history+
        [{"role": "user", "content": message}]
    )
   
    result = await Runner.run(first_chat_agent, messages)
    return str(result.final_output)

    # Run agent


# Blocks with ChatInterface and State
with gr.Blocks() as demo:
    gr.ChatInterface(fn=chat, title="An V-GRAM Bot")

demo.launch(ssr_mode=False)
