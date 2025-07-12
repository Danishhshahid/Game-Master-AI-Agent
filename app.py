"""
Fantasy Adventure Game with Chainlit Integration
A multi-agent text-based game using LiteLLM, Gemini, and Chainlit for web interface
"""

import random
import asyncio
import litellm
import os
import chainlit as cl
from typing import Dict, Any

# Set up LiteLLM for Gemini
litellm.set_verbose = False

# Game state will be stored in user session
DEFAULT_GAME_STATE = {
    "health": 100,
    "inventory": ["sword", "potion"],
    "location": "village",
    "in_combat": False,
    "enemy": None,
    "current_agent": "story_agent"
}

# Tool functions
def roll_dice():
    """Roll a 20-sided dice"""
    result = random.randint(1, 20)
    return result

def generate_event():
    """Generate a random event for the story"""
    events = [
        {"type": "monster", "name": "goblin", "description": "A goblin attacks!"},
        {"type": "monster", "name": "orc", "description": "An orc warrior appears!"},
        {"type": "treasure", "item": "magic ring", "description": "You find a treasure chest!"},
        {"type": "treasure", "item": "healing potion", "description": "You discover a hidden cache!"},
        {"type": "story", "description": "You meet a wise old wizard"},
        {"type": "story", "description": "You come across a mysterious merchant"}
    ]
    return random.choice(events)

# Agent functions
async def story_agent(player_action: str, game_state: Dict[str, Any], conversation_history: Dict) -> tuple:
    """Handles story and exploration"""
    
    # Check if player wants to give custom prompt
    if player_action.lower().startswith("prompt:"):
        custom_prompt = player_action[7:].strip()
        
        conversation_history["story_agent"].append({"role": "user", "content": custom_prompt})
        
        response = await litellm.acompletion(
            model="gemini/gemini-1.5-flash",
            messages=conversation_history["story_agent"],
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        ai_response = response.choices[0].message.content
        conversation_history["story_agent"].append({"role": "assistant", "content": ai_response})
        
        return f"🤖 **AI Response:** {ai_response}", "story_agent"
    
    # Normal game flow
    event = generate_event()
    
    # Create prompt for AI
    prompt = f"""
    You are telling a fantasy story. The player is in a {game_state['location']} with {game_state['health']} health.
    Player inventory: {game_state['inventory']}
    The player said: "{player_action}"
    A new event happened: {event['description']}
    
    Write 2-3 sentences about what happens next. Keep it simple and fun!
    """
    
    conversation_history["story_agent"].append({"role": "user", "content": prompt})
    
    response = await litellm.acompletion(
        model="gemini/gemini-1.5-flash",
        messages=conversation_history["story_agent"][-5:],
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    story = response.choices[0].message.content
    conversation_history["story_agent"].append({"role": "assistant", "content": story})
    
    result = f"📖 **Event:** {event['description']}\n\n📚 **Story:** {story}"
    
    # Check if we need to switch agents
    if event["type"] == "monster":
        game_state["in_combat"] = True
        game_state["enemy"] = event["name"]
        return result + "\n\n⚔️ **Combat initiated!**", "combat_agent"
    elif event["type"] == "treasure":
        game_state["inventory"].append(event["item"])
        return result + f"\n\n🎒 **Added {event['item']} to inventory!**", "item_agent"
    else:
        return result, "story_agent"

async def combat_agent(player_action: str, game_state: Dict[str, Any], conversation_history: Dict) -> tuple:
    """Handles fighting monsters"""
    
    # Check if player wants to give custom prompt
    if player_action.lower().startswith("prompt:"):
        custom_prompt = player_action[7:].strip()
        
        conversation_history["combat_agent"].append({"role": "user", "content": custom_prompt})
        
        response = await litellm.acompletion(
            model="gemini/gemini-1.5-flash",
            messages=conversation_history["combat_agent"],
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        ai_response = response.choices[0].message.content
        conversation_history["combat_agent"].append({"role": "assistant", "content": ai_response})
        
        return f"🤖 **AI Response:** {ai_response}", "combat_agent"
    
    # Normal combat flow
    player_roll = roll_dice()
    enemy_roll = roll_dice()
    
    prompt = f"""
    The player is fighting a {game_state['enemy']}!
    Player action: "{player_action}"
    Player rolled: {player_roll}
    Enemy rolled: {enemy_roll}
    Player health: {game_state['health']}
    
    Write 2-3 sentences about the fight. If player_roll > enemy_roll, player wins. 
    If enemy_roll > player_roll, player takes damage.
    """
    
    conversation_history["combat_agent"].append({"role": "user", "content": prompt})
    
    response = await litellm.acompletion(
        model="gemini/gemini-1.5-flash",
        messages=conversation_history["combat_agent"][-5:],
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    combat_story = response.choices[0].message.content
    conversation_history["combat_agent"].append({"role": "assistant", "content": combat_story})
    
    result = f"🎲 **Your roll:** {player_roll} | **Enemy roll:** {enemy_roll}\n\n⚔️ **Combat:** {combat_story}"
    
    # Update game based on dice rolls
    if player_roll > enemy_roll:
        result += "\n\n✅ **You won the fight!**"
        game_state["in_combat"] = False
        game_state["enemy"] = None
        return result, "story_agent"
    else:
        game_state["health"] -= 20
        result += f"\n\n❤️ **You took damage! Health: {game_state['health']}**"
        if game_state["health"] <= 0:
            result += "\n\n💀 **Game Over!**"
            return result, "game_over"
        return result, "combat_agent"

async def item_agent(player_action: str, game_state: Dict[str, Any], conversation_history: Dict) -> tuple:
    """Handles items and inventory"""
    
    # Check if player wants to give custom prompt
    if player_action.lower().startswith("prompt:"):
        custom_prompt = player_action[7:].strip()
        
        conversation_history["item_agent"].append({"role": "user", "content": custom_prompt})
        
        response = await litellm.acompletion(
            model="gemini/gemini-1.5-flash",
            messages=conversation_history["item_agent"],
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        ai_response = response.choices[0].message.content
        conversation_history["item_agent"].append({"role": "assistant", "content": ai_response})
        
        return f"🤖 **AI Response:** {ai_response}", "item_agent"
    
    # Normal item flow
    item_roll = roll_dice()
    
    prompt = f"""
    The player found an item! Their inventory has: {game_state['inventory']}
    Player action: "{player_action}"
    Item roll: {item_roll}
    Player health: {game_state['health']}
    
    Write 2-3 sentences about the item they found. If roll > 10, it's a great item!
    """
    
    conversation_history["item_agent"].append({"role": "user", "content": prompt})
    
    response = await litellm.acompletion(
        model="gemini/gemini-1.5-flash",
        messages=conversation_history["item_agent"][-5:],
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    item_story = response.choices[0].message.content
    conversation_history["item_agent"].append({"role": "assistant", "content": item_story})
    
    result = f"🎲 **Item roll:** {item_roll}\n\n🎒 **Item Discovery:** {item_story}"
    
    # Maybe heal player if they found something good
    if item_roll > 15:
        game_state["health"] = min(100, game_state["health"] + 30)
        result += f"\n\n✨ **You feel better! Health: {game_state['health']}**"
    
    return result, "story_agent"

# Chainlit event handlers
@cl.on_chat_start
async def start():
    """Initialize the game when chat starts"""
    # Initialize game state and conversation history
    cl.user_session.set("game_state", DEFAULT_GAME_STATE.copy())
    cl.user_session.set("conversation_history", {
        "story_agent": [],
        "combat_agent": [],
        "item_agent": []
    })
    
    welcome_message = """
# 🎮 Welcome to Fantasy Adventure Game!

🤖 **Powered by Google's Gemini 1.5 Flash model!**

## How to Play:
- Type your actions naturally (e.g., "I explore the forest", "I attack the goblin")
- Type `status` to see your current health and inventory
- Type `history` to see recent conversation history
- Type `restart` to start a new game
- Type `prompt: your message` to give custom prompts directly to the AI

## Special Commands:
- **status** - Show current game state
- **history** - Show conversation history
- **restart** - Start a new game
- **prompt: [message]** - Send custom prompt to AI

**Your adventure begins in a peaceful village...**
"""
    
    await cl.Message(content=welcome_message).send()
    
    # Send initial status
    game_state = cl.user_session.get("game_state")
    status_msg = f"❤️ **Health:** {game_state['health']} | 🎒 **Inventory:** {', '.join(game_state['inventory'])} | 📍 **Location:** {game_state['location']}"
    await cl.Message(content=status_msg).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages"""
    user_input = message.content.strip()
    
    # Get game state and history from session
    game_state = cl.user_session.get("game_state")
    conversation_history = cl.user_session.get("conversation_history")
    
    # Handle special commands
    if user_input.lower() == "status":
        status_msg = f"""
**Current Status:**
❤️ **Health:** {game_state['health']}
🎒 **Inventory:** {', '.join(game_state['inventory'])}
📍 **Location:** {game_state['location']}
🤖 **Current Agent:** {game_state['current_agent']}
⚔️ **In Combat:** {'Yes' if game_state['in_combat'] else 'No'}
"""
        await cl.Message(content=status_msg).send()
        return
    
    elif user_input.lower() == "history":
        current_agent = game_state['current_agent']
        history_msg = f"📚 **Conversation History for {current_agent}:**\n\n"
        
        for i, msg in enumerate(conversation_history[current_agent][-6:]):
            role = "You" if msg["role"] == "user" else "AI"
            content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
            history_msg += f"{i+1}. **{role}:** {content}\n\n"
        
        await cl.Message(content=history_msg).send()
        return
    
    elif user_input.lower() == "restart":
        # Reset game state
        cl.user_session.set("game_state", DEFAULT_GAME_STATE.copy())
        cl.user_session.set("conversation_history", {
            "story_agent": [],
            "combat_agent": [],
            "item_agent": []
        })
        await cl.Message(content="🔄 **Game restarted!** Your adventure begins anew in the village.").send()
        return
    
    # Handle game logic
    current_agent = game_state['current_agent']
    
    try:
        # Show thinking message
        thinking_msg = cl.Message(content=f"🤖 **{current_agent.replace('_', ' ').title()} is thinking...**")
        await thinking_msg.send()
        
        # Call appropriate agent
        if current_agent == "story_agent":
            result, next_agent = await story_agent(user_input, game_state, conversation_history)
        elif current_agent == "combat_agent":
            result, next_agent = await combat_agent(user_input, game_state, conversation_history)
        elif current_agent == "item_agent":
            result, next_agent = await item_agent(user_input, game_state, conversation_history)
        else:
            result = "💀 **Game Over!** Type `restart` to play again."
            next_agent = "game_over"
        
        # Update thinking message with result
        thinking_msg.content = result
        await thinking_msg.update()
        
        # Update game state
        game_state['current_agent'] = next_agent
        
        # Show updated status if significant changes
        if game_state['health'] != DEFAULT_GAME_STATE['health'] or len(game_state['inventory']) > 2:
            status_msg = f"❤️ **Health:** {game_state['health']} | 🎒 **Inventory:** {', '.join(game_state['inventory'])}"
            await cl.Message(content=status_msg).send()
        
        # Save updated state
        cl.user_session.set("game_state", game_state)
        cl.user_session.set("conversation_history", conversation_history)
        
    except Exception as e:
        await cl.Message(content=f"❌ **Error:** {str(e)}\n\nMake sure your GOOGLE_API_KEY is set correctly!").send()

if __name__ == "__main__":
    # Instructions for running
    print("🚀 To run this game:")
    print("1. Install dependencies: pip install chainlit litellm")
    print("2. Set your Google API key: export GOOGLE_API_KEY=your_api_key_here")
    print("3. Run: chainlit run this_file.py")
    print("4. Open your browser to the URL shown")