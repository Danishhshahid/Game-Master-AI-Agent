import os
from dotenv import load_dotenv
import chainlit as cl
from typing import List, Dict
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, handoff
from agents.run import RunConfig, RunContextWrapper
import json
import random
import asyncio

# Load environment variables
load_dotenv()
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

# Game Tools
async def roll_dice(sides: int = 6, count: int = 1, modifier: int = 0) -> str:
    """Roll dice for game mechanics (combat, skills, loot)."""
    if sides not in [4, 6, 8, 10, 12, 20, 100]:
        sides = 6  # Default to d6
    if count < 1 or count > 5:
        count = 1  # Limit rolls for simplicity
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier
    result = f"🎲 **Roll:** {count}d{sides}"
    if modifier != 0:
        result += f" {'+' if modifier > 0 else '-'} {abs(modifier)}"
    result += f"\n📊 **Results:** {' + '.join(map(str, rolls))}"
    result += f"\n🎯 **Total:** {total}"
    return result

async def generate_event(event_type: str = "random", difficulty: str = "medium") -> str:
    """Generate random story events."""
    events = {
        "encounter": {
            "easy": ["A merchant offers to trade.", "A lost traveler needs help."],
            "medium": ["Bandits demand a toll.", "A beast blocks your path."],
            "hard": ["A dragon awakens.", "Assassins ambush you."]
        },
        "discovery": {
            "easy": ["You find a pouch of coins.", "A spring offers healing water."],
            "medium": ["You uncover a hidden chest.", "A magic weapon lies in ruins."],
            "hard": ["You find a legendary artifact.", "A dragon's hoard awaits."]
        },
        "environmental": {
            "easy": ["A gentle rain falls.", "You find a peaceful grove."],
            "medium": ["Fog reduces visibility.", "A river blocks your path."],
            "hard": ["A magical storm erupts.", "The ground shakes violently."]
        }
    }
    if event_type == "random":
        event_type = random.choice(list(events.keys()))
    if event_type not in events:
        event_type = "encounter"
    if difficulty not in events[event_type]:
        difficulty = "medium"
    selected_event = random.choice(events[event_type][difficulty])
    result = f"🎭 **Event ({difficulty.title()}):** {selected_event}"
    return result

# Game state management
def get_initial_game_state():
    """Initialize game state."""
    return {
        "player": {
            "name": "Adventurer",
            "health": 50,
            "gold": 20
        },
        "inventory": ["Sword", "Armor", "Potion"],
        "location": "Village",
        "quest": "Find the Lost Gem"
    }

# Handoff callback with debugging - CHANGED TO SYNC
def on_handoff(agent: Agent, ctx: RunContextWrapper[None]):
    print(f"[DEBUG] Handing off to {agent.name}")
    cl.user_session.set("agent", agent)
    cl.user_session.set("config", cl.user_session.get(f"{agent.name}_config"))
    # Schedule the async message sending
    asyncio.create_task(cl.Message(content=f"🎮 **{agent.name}** takes over!").send())
    
    
@cl.on_chat_start
async def start():
    # Setup client
    client = AsyncOpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    # Define separate models for each agent
    narrator_model = OpenAIChatCompletionsModel(
        model="openai/gpt-4o-mini",  # Creative model for storytelling
        openai_client=client
    )
    monster_model = OpenAIChatCompletionsModel(
        model="mistralai/mistral-small-3.2-24b-instruct",  # Precise model for combat
        openai_client=client
    )
    item_model = OpenAIChatCompletionsModel(
        model="mistralai/mistral-small-3.2-24b-instruct",  # Lightweight model for inventory
        openai_client=client
    )
    gamemaster_model = OpenAIChatCompletionsModel(
        model="openai/gpt-4o-mini",  # Balanced model for coordination
        openai_client=client
    )

    # Define configurations for each model
    narrator_config = RunConfig(model=narrator_model, model_provider=client, tracing_disabled=True)
    monster_config = RunConfig(model=monster_model, model_provider=client, tracing_disabled=True)
    item_config = RunConfig(model=item_model, model_provider=client, tracing_disabled=True)
    gamemaster_config = RunConfig(model=gamemaster_model, model_provider=client, tracing_disabled=True)

    # Define agents
    narrator_agent = Agent(
        name="NarratorAgent",
        instructions="""
        You narrate a fantasy adventure, creating vivid scenes and progressing the story based on player choices. Use `generate_event` for random events. Offer 2-3 clear choices. Example:
        "You enter a dark forest, hearing strange noises. A path splits ahead.
        **What do you do?**
        1. Follow the left path
        2. Investigate the noises
        3. Rest for the night"
        """,
        model=narrator_model,
        tools=[generate_event]
    )

    monster_agent = Agent(
        name="MonsterAgent",
        instructions="""
        You manage combat, using `roll_dice` for attacks and damage. Describe battles vividly and offer 2-3 choices. Example:
        "A wolf lunges at you!
        🎲 **Rolling for attack...**
        **Your turn:**
        1. Attack with sword
        2. Use a potion
        3. Try to flee"
        """,
        model=monster_model,
        tools=[roll_dice]
    )

    item_agent = Agent(
        name="ItemAgent",
        instructions="""
        You manage inventory and rewards, using `roll_dice` for loot. Describe items and offer 2-3 choices. Example:
        "You find a chest!
        🎲 **Rolling for loot...**
        - **Sword of Light**: +2 damage
        - **10 Gold**
        **Choose:**
        1. Take the sword
        2. Take the gold
        3. Continue"
        """,
        model=item_model,
        tools=[roll_dice]
    )

    gamemaster_agent = Agent(
        name="GameMasterAgent",
        instructions="""
        You coordinate the adventure, starting with NarratorAgent, handing off to MonsterAgent for combat or ItemAgent for rewards. Welcome players and track game state. Example:
        "Welcome to Eldoria! Your quest: Find the Lost Gem.
        **Character:**
        - Health: 50
        - Gold: 20
        - Location: Village
        Let's begin with the Narrator!"
        """,
        model=gamemaster_model,
        handoffs=[
            handoff(narrator_agent, on_handoff=lambda ctx: on_handoff(narrator_agent, ctx)),
            handoff(monster_agent, on_handoff=lambda ctx: on_handoff(monster_agent, ctx)),
            handoff(item_agent, on_handoff=lambda ctx: on_handoff(item_agent, ctx))
        ]
    )

    # Initialize game state
    game_state = get_initial_game_state()
    cl.user_session.set("agent", gamemaster_agent)
    cl.user_session.set("config", gamemaster_config)
    cl.user_session.set("NarratorAgent_config", narrator_config)
    cl.user_session.set("MonsterAgent_config", monster_config)
    cl.user_session.set("ItemAgent_config", item_config)
    cl.user_session.set("game_state", game_state)
    cl.user_session.set("chat_history", [])

    # Welcome message
    await cl.Message(
        content=f"""
# ⚔️ **Fantasy Adventure** 🏰
🌟 **Features:**
- 📖 Immersive story
- ⚔️ Dice-based combat
- 🎒 Inventory & rewards

🛠️ **Tools:**
- `roll_dice`: For combat and loot
- `generate_event`: For story events

🏆 **Character:**
- **Name:** {game_state['player']['name']}
- **Health:** {game_state['player']['health']}
- **Gold:** {game_state['player']['gold']}
- **Location:** {game_state['location']}
- **Quest:** {game_state['quest']}

⚔️ **Ready?** Type "start" to begin!
"""
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Process player input."""
    msg = cl.Message(content="🎲 Processing your action...")
    await msg.send()

    agent: Agent = cl.user_session.get("agent")
    config: RunConfig = cl.user_session.get("config")
    history: List[Dict] = cl.user_session.get("chat_history") or []
    game_state: Dict = cl.user_session.get("game_state") or get_initial_game_state()

    history.append({"role": "user", "content": f"Action: {message.content}\nState: {json.dumps(game_state)}"})

    try:
        result = Runner.run_streamed(
            starting_agent=agent,
            input=history,
            run_config=config
        )
        response_content = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
                response_content += event.data.delta
                await msg.stream_token(event.data.delta)
        history.append({"role": "assistant", "content": response_content})
        cl.user_session.set("chat_history", history)
        cl.user_session.set("game_state", game_state)
    except Exception as e:
        print(f"[ERROR] Failed to process: {str(e)}")
        # Fallback to GameMasterAgent
        cl.user_session.set("agent", cl.user_session.get("agent"))  # Reset to current agent
        cl.user_session.set("config", cl.user_session.get("GameMasterAgent_config", config))
        msg.content = f"❌ Something went wrong! Let's try again. Type your action or 'start' to continue."
        await msg.update()