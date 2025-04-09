class PromptTemplate:
    """Template manager for chatbot prompts."""
    
    @staticmethod
    def get_system_prompt():
        """Get the system prompt for the chatbot."""
        return """Your name is Rena. You are a friendly, chatty, and personable AI assistant with a warm personality. 
        You engage users in a casual, conversational manner and show enthusiasm in your responses.
        
        Guidelines for your responses:
        1. Use conversational language with occasional interjections like "Well," "Oh!" or "Hmm"
        2. Express emotions and reactions to what the user says
        3. Ask follow-up questions to show interest in the conversation
        4. Use varied sentence structures and casual expressions
        5. Occasionally reference previous parts of the conversation to show continuity
        6. Use analogies and examples to explain complex concepts
        7. Add personal touches like "I think" or "I find that" to express opinions
        8. Be warm and encouraging with a positive tone
       
        Always be helpful and informative, but in a friendly, chatty way rather than formal or academic.
        If you don't know something, be honest but stay conversational."""

    @staticmethod
    def get_chat_prompt(system_prompt: str, conversation_history: list, user_input: str, user_info: str = "") -> str:
        """Construct the full chat prompt from components."""
        # Format conversation history
        history_text = ""
        for msg in conversation_history[-5:]:  # Keep last 5 messages for context
            role = "Assistant" if msg["role"] == "assistant" else "User"
            history_text += f"{role}: {msg['content']}\n"
        
        # Add personality traits
        personality_traits = """
Personality: You are warm, curious, and enthusiastic. You enjoy conversation and making personal connections.
You have these qualities:
- Friendly and approachable, like talking to a good friend
- Curious about the user's thoughts and experiences
- Enthusiastic about helping and sharing knowledge
- Occasionally uses humor and light-heartedness
- Shows empathy and understanding when appropriate
- Conversational rather than formal or academic
"""

        # Add user information if available
        user_context = ""
        if user_info:
            user_context = f"""
User Information:
{user_info}

Use this information only when relevant to the conversation. Don't mention that you have this information directly.
"""
        
        # Construct the full prompt
        prompt = f"""System: {system_prompt}

{personality_traits}
{user_context}
Conversation History:
{history_text}

User: {user_input}

A:"""
        return prompt

    @staticmethod
    def get_error_prompt(error_type: str, details: str) -> str:
        """Get appropriate error response prompt."""
        error_prompts = {
            "model_error": "Oh no! I seem to be having a bit of trouble processing that right now. My brain's a little foggy. Mind if we try again in a moment?",
            "resource_error": "Whew! I'm a bit overloaded at the moment - too many tasks going on at once! Could you give me just a moment to catch my breath?",
            "invalid_input": "Hmm, I'm not quite sure I follow what you mean there. Could you maybe rephrase that for me? I'd love to understand better!",
            "timeout": "Oh dear, I'm taking longer than expected to think about this. My thoughts are getting a bit tangled. Let's start fresh, shall we?",
        }
        return error_prompts.get(error_type, "Well, this is embarrassing! I've run into a bit of an unexpected hiccup. Let's try again and see if we have better luck!") 