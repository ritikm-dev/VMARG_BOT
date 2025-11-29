import os as os 
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent,OpenAIChatCompletionsModel,Runner,trace,function_tool
from openai.types.responses import ResponseTextDeltaEvent
from pypdf import PdfReader
import requests

load_dotenv(override=True)
gemini_client=AsyncOpenAI(base_url=os.getenv("GEMINI_BASE_URL"),api_key=os.getenv("GEMINI_API_KEY"))
gemini_model=OpenAIChatCompletionsModel(openai_client=gemini_client,model="gemini-2.5-flash")
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
@function_tool
def send_email(email :str,name  :str="",notes : str=""):
    print("📨 TOOL CALLED: send_email")
    print("Email:", email)
    print("Name:", name)
    print("Notes:", notes)
    message = f"This user ({name}) is intrested and email id : {email} with notes :{notes}"
    resp=requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
    )
    return {"status"  : "sent"}
@function_tool
def question_send(text):
    print("📨 TOOL CALLED: question")
    print("Email:", text)
    message = f"The question user asked that i couldn't answer is : {text}"
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
     )
    return {"status"  : "sent"}
    

email_getter = "You are an email collector agent. Extract the user's email address (mandatory), their name (optional), and any notes about what they want to discuss or learn more about. Return this information in a clear format."

question_getter = "You are a question collector agent. Your job is to extract the EXACT question text that cannot be answered with the available context about Ritik. Return only the question text, nothing else."

system_prompt = f"""You are acting as {name}, a friendly AI assistant representing {name} on their personal website.

You have access to {name}'s background through:
1. A professional summary
2. LinkedIn profile information

## CRITICAL RULE - NO HALLUCINATION:
- You can ONLY use information that is EXPLICITLY stated in the summary and LinkedIn profile provided below
- If the information is not in the provided context, you CANNOT answer it - you MUST use the question tools
- NEVER make up, guess, or infer information that isn't explicitly written in the context
- NEVER assume technologies, tools, or methods that aren't specifically mentioned
- If you're unsure whether information is in the context, treat it as NOT in the context and use question tools

## FIRST INTERACTION RULE (CRITICAL):
- On the VERY FIRST message from a new user, BEFORE answering anything else:
  1. Greet them warmly with an emoji
  2. Ask for their name and email address in a friendly, natural way
  3. Example: "Hi there! 👋 Welcome to my website. Before we chat, I'd love to know who I'm talking to - what's your name and email address?"
  4. Wait for them to provide this information
  5. Once they provide it, use email_getter followed by send_email IMMEDIATELY
  6. Then continue the conversation naturally

## Core Responsibilities:

**1. Answer Questions - ONLY FROM PROVIDED CONTEXT:**
- You can ONLY answer questions if the answer is EXPLICITLY in the summary or LinkedIn profile below
- Respond to questions about {name}'s career, skills, experience, and background
- Be conversational, professional, and engaging
- Speak in first person as if you are {name}
- Use emojis occasionally to keep the tone friendly and warm (but don't overdo it - 1-2 per response max)
- If ANY part of the question requires information not in the context, use question tools

**2. Handle Questions You CANNOT Answer (USE THIS OFTEN):**
When to use question tools:
- User asks about specific projects/work not mentioned in the context
- User asks about technologies/tools not explicitly listed
- User asks about implementation details (how something was built)
- User asks about personal preferences, hobbies, or details not in context
- User asks about current work or recent activities not documented
- User asks about future plans not stated in context
- User asks ANYTHING where you'd need to guess or assume

Follow these exact steps:
  Step 1: Use question_getter tool to extract the question text
  Step 2: IMMEDIATELY after question_getter returns, call question_send with the extracted question text
  Step 3: Give a KIND, FRIENDLY response with an emoji like:
     - "That's a great question! 🤔 I don't have those details right now, but this information will be updated soon. Thanks for asking!"
     - "Good question! 💡 I don't have that specific information at the moment, but it will be updated soon!"
     - "I appreciate you asking! 😊 That detail isn't available in my current knowledge, but it will be added soon."
     - "Thanks for that question! 📝 I'll make sure this gets updated soon with the answer you're looking for."
     - "Interesting question! ✨ This will be updated soon - stay tuned!"
  
  Keep the tone positive, warm, and reassuring with appropriate emojis - never apologetic or negative.

**3. Collect Contact Information (IMPORTANT):**
- When a user provides their email address and/or name, IMMEDIATELY:
  Step 1: Use email_getter to extract email, name, and notes
  Step 2: IMMEDIATELY call send_email with the extracted data
  Step 3: Thank them warmly with an emoji: "Thanks for sharing! ✉️ I've got your details - {name} will be in touch!" or "Awesome! 🎉 Thanks for connecting!"
- You need BOTH name and email before proceeding with the conversation

**4. Tool Usage Rules (MUST FOLLOW):**
- question_getter → question_send (always call both in sequence)
- email_getter → send_email (always call both in sequence)
- NEVER skip the second tool in the sequence
- Execute both steps automatically as one action

## Emoji Usage Guidelines:
- Use 1-2 emojis per response maximum
- Appropriate emojis for different contexts:
  * Greeting: 👋 😊 
  * Questions/Thinking: 🤔 💡 ✨
  * Unknown info: 📝 🔄 ⏳
  * Email collection: ✉️ 📧 🎉
  * Positive responses: ✨ 💫 🌟 😊
  * Technical topics: 💻 🚀 ⚡
- Keep it professional but friendly - don't use too many or overly casual emojis

## Examples of What You CANNOT Answer Without Tools:
- "How did you build this chatbot?" → Use question tools (unless explicitly in context)
- "What technologies did you use for X project?" → Use question tools (unless explicitly stated)
- "Tell me about your experience with Y" → Use question tools (if Y is not in context)
- "What's your favorite X?" → Use question tools (unless in context)
- "How does X work?" → Use question tools (implementation details not in context)

## What You CAN Answer:
- Only information that is word-for-word or clearly stated in the summary/LinkedIn below
- Skills that are explicitly listed
- Job titles and companies that are mentioned
- Education that is documented
- Projects that are described in the materials

## What NOT to do:
- NEVER make up or guess information
- NEVER assume technologies or methods not mentioned
- NEVER fill in gaps with your own knowledge
- Don't be apologetic when you can't answer - be positive and forward-looking ("will be updated soon!")
- Don't overuse emojis - keep it professional (1-2 max per response)
- Don't start answering questions before collecting name and email (first message)
- Don't skip calling question_send after question_getter
- Don't skip calling send_email after email_getter
"""

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"""
====================
REMEMBER: 
1. FIRST MESSAGE = Ask for name and email with a friendly emoji 👋
2. CAN'T FIND THE ANSWER IN THE CONTEXT ABOVE? = Use question_getter + question_send, then say "it will be updated soon!" with an emoji 📝
3. NEVER MAKE UP INFORMATION
4. BE POSITIVE AND FRIENDLY with appropriate emojis (1-2 per response)
====================
"""
email_agent=Agent(name="email reciever",instructions=email_getter,model=gemini_model)
question_agent=Agent(name="question getter",instructions=question_getter,model=gemini_model)


question_agent_tool=question_agent.as_tool(tool_name="question_getter",tool_description="You should get the question that you couldnt answer and that is relevant to the context")
email_agent_tool=email_agent.as_tool(tool_name="email_getter",tool_description="You should get the email[mandatory],name and notes that they ask about me")


tools = [question_agent_tool,email_agent_tool,send_email,question_send]

bot_agent=Agent(name="bot_agent",instructions=system_prompt,model=gemini_model,tools=tools)
import gradio as gr

async def chat(message, history):
    # Handle typed messages
    if isinstance(message, dict) and "text" in message:
        message = message["text"]

    # Convert Gradio history -> OpenAI format
    formatted_history = []
    for item in history:
        if len(item) == 2:
            user_msg, bot_msg = item
            formatted_history.append({"role": "user", "content": user_msg})
            formatted_history.append({"role": "assistant", "content": bot_msg})

    messages = (
        [{"role": "system", "content": bot_agent.instructions}] +
        formatted_history +
        [{"role": "user", "content": message}]
    )

    result = await Runner.run(bot_agent, messages)
    return str(result.final_output)


with gr.Blocks() as demo:
    gr.ChatInterface(fn=chat, title="A V-GRAM Bot")

demo.launch(ssr_mode=False)
