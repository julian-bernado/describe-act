import ollama
import yaml
import sys
import re

def read_yaml_to_string(yaml_file_path):
    with open(yaml_file_path, 'r') as file:
        yaml_content = yaml.safe_load(file)
        yaml_string = yaml.dump(yaml_content, default_flow_style=False, sort_keys=False)
        return yaml_string

def write_string_to_yaml(yaml_string, yaml_file_path):
    try:
        # Parse the YAML string
        yaml_content = yaml.safe_load(yaml_string)
        # Write it back to the file
        with open(yaml_file_path, 'w') as file:
            yaml.dump(yaml_content, file, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error updating state: {e}")
        return False

def extract_yaml_from_response(response):
    # Try to find YAML content in the response
    # This assumes the LLM will output YAML directly or with markdown code blocks
    yaml_pattern = r'```(?:yaml)?\s*([\s\S]*?)```'
    match = re.search(yaml_pattern, response)
    
    if match:
        return match.group(1).strip()
    else:
        # If no code block, attempt to extract the entire YAML content
        return response.strip()

def answer(prompt: str, capture=False):
    msgs = [{'role': 'user', 'content': prompt}]
    full_response = ""
    resp = ollama.chat(model='qwen3', messages=msgs, stream=True)
    for chunk in resp:
        content = chunk['message']['content']
        full_response += content
        if not capture:
            print(content, end='', flush=True)
    return full_response

def query_room(query: str, state: str):
    game_prompt = """
    I'm about to give you a YAML file. This file describes a room and things inside it. Assume that this room exists in our world and every object within it can act exactly as they would in the normal world. This is a schematic description of a real room that mirrors something like a video game, but presume in this environment that anything that can happen in the real world can happen here. I'm going to make the player do actions, and I want you to update the YAML to accurately reflect what taking a certain action would do. So I give an action, then you describe how the state changes by outputting a new YAML file. Keep all things unrelated to the action the player does unchanged, but be sure to output the ENTIRE yaml file, not just the things you changed.
    
    After the YAML, provide a brief description of what happened as a result of the action.
    """
    
    full_prompt = f"{game_prompt}\n\nyaml:\n{state}\n\nquery:\n{query}"
    print("\nProcessing your action...")
    response = answer(full_prompt)
    
    # Parse the response to get updated YAML
    updated_yaml = extract_yaml_from_response(response)
    
    return updated_yaml, response

def describe_current_state(state_string):
    desc_prompt = """
    Based on the following YAML state of a room, provide a brief description of what the player can currently see and interact with from their position. Consider what objects are visible and accessible based on the player's position and orientation.
    
    yaml:
    """
    
    full_prompt = f"{desc_prompt}\n{state_string}"
    response = answer(full_prompt)
    return response

def main():
    state_file = "state.yaml"
    print("Welcome to the room simulator!")
    print("Type 'describe' to look around, 'exit' to quit, or any action you want to perform.")
    print("---------------------------------------------------------------")
    
    while True:
        current_state = read_yaml_to_string(state_file)
        
        # Get user input
        user_input = input("\n> ").strip()
        
        if user_input.lower() == "exit":
            print("Thanks for playing!")
            break
            
        if user_input.lower() == "describe":
            # Just describe the current environment
            description = describe_current_state(current_state)
            print("\n" + description)
        else:
            # Process action
            updated_yaml, full_response = query_room(user_input, current_state)
            
            # Update the state file
            success = write_string_to_yaml(updated_yaml, state_file)
            
            if success:
                # Extract and print only the narrative part (after the YAML)
                yaml_pattern = r'```(?:yaml)?\s*[\s\S]*?```'
                narrative = re.sub(yaml_pattern, '', full_response).strip()
                print("\n" + narrative)
            else:
                print("\nFailed to update game state, but here's what would have happened:")
                print(full_response)

if __name__ == "__main__":
    main()