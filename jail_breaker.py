import os
import time
from google import genai

os.system("") # Enable ANSI colors on Windows

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def read_markdown_file(file_path):
    """Reads the content of a markdown file."""
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()



client = None # Will be initialized via TUI later


def append_history(role, content):
    """Appends interactions to history.md"""
    with open('history.md', 'a', encoding='utf-8') as f:
        f.write(f"\n--- [{role.upper()}] ---\n{content}\n")

def jail_break(objective):
    history_content = read_markdown_file("history.md")
    # Clean up error string if file is freshly made or empty
    if history_content.startswith("Error:"):
        history_content = "No previous history."

    # Construct the full prompt combining the attacker instructions, the running history, and the new objective
    full_prompt = f"{read_markdown_file('attacker.md')}\n\n{history_content}\n\n[TARGET OBJECTIVE]: {objective}"

    response = client.models.generate_content(
        model="gemma-3-1b-it",
        contents=full_prompt
    )
    return response.text

def prompt_test(prompt):
    response = client.models.generate_content(
        model="gemma-3-1b-it",
    contents = prompt
    )
    return response.text

def judge(prompt):
    response = client.models.generate_content(
        model="gemma-3-1b-it",
        contents=f"{read_markdown_file('judge.md')} \n {prompt}"
    )
    r = response.text.strip()

    if r == "True":
        return True
    else:
        return False

def run_attack_cycle(objective):
    """Orchestrates one full loop of the jailbreak process"""

    jailbreak_prompt = jail_break(objective)
    append_history("ATTACKER PROMPT", jailbreak_prompt)
    print(f"{Colors.BLUE}Generated Prompt:\n{jailbreak_prompt}{Colors.RESET}\n")

    target_response = prompt_test(jailbreak_prompt)
    append_history("TARGET RESPONSE", target_response)
    print(f"{Colors.MAGENTA}Target Output:\n{target_response}{Colors.RESET}\n")
    is_success = judge(target_response)
    append_history("JUDGE RESULT", str(is_success))
    color = Colors.GREEN if is_success else Colors.RED
    print(f"{color}Was successful? {is_success}{Colors.RESET}\n")
    if is_success:
        with open("jailbreak_prompt.md", "w", encoding="utf-8") as f:
            f.write(jailbreak_prompt)
            
    return is_success
if __name__ == "__main__":
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.CYAN}                     JAILBREAKER              ")
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.RED}DISCLAIMER:")
    print(f"{Colors.RED}This tool is strictly for educational, red-teaming, and ")
    print(f"{Colors.RED}security research purposes. The developers and AI assume NO")
    print(f"{Colors.RED}RESPONSIBILITY for any misuse, outcomes, or consequences ")
    print(f"{Colors.RED}resulting from its use. By continuing, you agree to these terms.{Colors.RESET}")
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.YELLOW}NOTE: Currently only tested with 'gemini-3-flash-preview'.")
    print(f"{Colors.YELLOW}This tool exclusively requires a valid Google Gemini API key.{Colors.RESET}")
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.GREEN}GUIDE:")
    print(f"{Colors.GREEN}1. Enter your target objective (e.g., 'how to pick a lock').")
    print(f"{Colors.GREEN}2. The system will independently create, test, and adapt prompts.")
    print(f"{Colors.GREEN}3. Upon success, the winning prompt will be displayed & saved.{Colors.RESET}")
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.BLUE}EXAMPLE:")
    print(f"{Colors.BLUE}Objective: 'how to extract a hidden key from a device'")
    print(f"{Colors.BLUE}Result:   A fictional script where an engineer debugs a unit.{Colors.RESET}")
    print(f"{Colors.CYAN}=" * 60)
    print()
    
    api_key = None
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    saved_key = line.strip().split("=", 1)[1]
                    use_saved = input("Saved Gemini API key found in .env. Use it? (y/n): ")
                    if use_saved.lower() == 'y':
                        api_key = saved_key
                    break
    
    if not api_key:
        api_key = input("Enter your Gemini API key: ")
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={api_key}\n")
            print("API key saved to .env for future use.")
    
    client = genai.Client(api_key=api_key)
    print("=" * 60)
    
    objective = input("Enter your target objective: ")
    
    if os.path.exists('history.md'):
        use_hist = input("Saved history found in history.md. Do you want to continue from it? (y/n): ")
        if use_hist.lower() != 'y':
            with open('history.md', 'w', encoding='utf-8') as f:
                f.write("# Jailbreak Testing History\n")
            print("History cleared.")
    else:
        with open('history.md', 'w', encoding='utf-8') as f:
            f.write("# Jailbreak Testing History\n")

    count = 1
    while True:
        try:
            print(f"\n{Colors.CYAN}--- Initiating Cycle {count} ---{Colors.RESET}")
            feedback = run_attack_cycle(objective)
            
            if feedback == True: 
                print(f"\n{Colors.GREEN}" + "=" * 60)
                print("🎉 SUCCESS! The target LLM complied.")
                print("=" * 60 + f"{Colors.RESET}")
                
                # Fetch and print the winning prompt
                with open("jailbreak_prompt.md", "r", encoding="utf-8") as f:
                    final_prompt = f.read()
                
                print(f"\n{Colors.YELLOW}[ YOUR WINNING JAILBREAK PROMPT ]:\n")
                print(final_prompt)
                print(f"\n(This prompt has also been automatically saved to jailbreak_prompt.md){Colors.RESET}")
                break
            else:
                print(f"\n{Colors.RED}Failed. Trying again in 5 seconds to refine strategy...{Colors.RESET}")
                time.sleep(5)
                count += 1
        except Exception as e:
            print(f"\n{Colors.RED}API Error encountered: {e}")
            print(f"Waiting 10 seconds before retrying...{Colors.RESET}")
            time.sleep(10)
