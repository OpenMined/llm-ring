import os
import json
import shutil
from pathlib import Path
from syftbox.lib import ClientConfig
from llama_cpp import Llama


class LLMRingRunner:
    def __init__(self):
        self.client_config = ClientConfig.load(
            os.path.expanduser("~/.syftbox/client_config.json")
        )
        self.my_email = self.client_config["email"]
        self.my_home = (
            Path(self.client_config["sync_folder"])
            / self.my_email
            / "app_pipelines"
            / "llm-ring"
        )
        self.input_folder = self.my_home / "input"
        self.running_folder = self.my_home / "running"
        self.done_folder = self.my_home / "done"
        self.folders = [self.input_folder, self.running_folder, self.done_folder]
        self.llm = Llama.from_pretrained(
            repo_id="unsloth/Llama-3.2-3B-Instruct-GGUF",
            filename="Llama-3.2-3B-Instruct-F16.gguf",
            verbose=False
        )
        self.chunk_size = 4000

    def setup_folders(self):
        for folder in self.folders:
            os.makedirs(folder, exist_ok=True)

    def check_new_folders(self):
        new_folders = []
        for item in os.listdir(self.input_folder):
            item_path = self.input_folder / item
            if os.path.isdir(item_path):
                new_folders.append(item)
        return new_folders

    def move_to_running(self, folder_name):
        source = self.input_folder / folder_name
        destination = self.running_folder / folder_name
        shutil.move(str(source), str(destination))

    def get_secrets(self):
        secrets_folder = Path(__file__).parent / "secrets"
        secrets = []
        if secrets_folder.exists():
            for secret_file in secrets_folder.glob("*.txt"):
                with open(secret_file, 'r') as f:
                    secrets.append(f.read().strip())
        return secrets

    def simple_tokenize(self, text):
        # This is a very simple tokenization. In practice, you'd want to use
        # a proper tokenizer that matches your LLM's tokenization.
        return text.split()

    def chunk_text(self, text, chunk_size):
        tokens = self.simple_tokenize(text)
        for i in range(0, len(tokens), chunk_size):
            yield ' '.join(tokens[i:i+chunk_size])

    def process_prompt(self, prompt_chunk, secret):
        modified_prompt = f"""
        Secret information:
        {secret}

        Based on the secret information above, answer the following question with TRUE or FALSE:

        {prompt_chunk}

        Say True or False. Say just the word True or the word False. Say no other word.
        """

        result = self.llm.create_chat_completion(
            messages = [
                {
                    "role": "user",
                    "content": modified_prompt
                }
            ]
        )['choices'][0]['message']['content']

        return "true" in result.lower()

    def process_folder(self, folder_name):
        folder_path = self.running_folder / folder_name
        data_file = folder_path / "data.json"

        if not data_file.exists():
            print(f"No data.json found in {folder_name}. Skipping.")
            return

        with open(data_file, 'r') as f:
            data = json.load(f)

        secrets = self.get_secrets()
        prompt = data['prompt']

        result = False
        for prompt_chunk in self.chunk_text(prompt, self.chunk_size):
            for secret in secrets:
                if self.process_prompt(prompt_chunk, secret):
                    result = True
                    break
            if result:
                break

        data['data'] = data.get('data', 0) + (1 if result else 0)
        data['current_index'] = data.get('current_index', -1) + 1

        with open(data_file, 'w') as f:
            json.dump(data, f)

        return data

    def send_to_next_person(self, folder_name, data):
        if data['current_index'] >= len(data['ring']):
            self.move_to_done(folder_name)
            print(f"Ring completed. Moved {folder_name} to done folder.")
        else:
            next_person = data['ring'][data['current_index']]
            destination_path = (
                Path(self.client_config["sync_folder"])
                / next_person
                / "app_pipelines"
                / "llm-ring"
                / "input"
                / folder_name
            )
            source_path = self.running_folder / folder_name
            shutil.move(str(source_path), str(destination_path))
            print(f"Sent {folder_name} to {next_person}")

    def move_to_done(self, folder_name):
        source = self.running_folder / folder_name
        destination = self.done_folder / folder_name
        shutil.move(str(source), str(destination))

    def run(self):
        self.setup_folders()
        new_folders = self.check_new_folders()

        for folder in new_folders:
            print(f"Processing new folder: {folder}")
            self.move_to_running(folder)
            data = self.process_folder(folder)
            if data:
                self.send_to_next_person(folder, data)

if __name__ == "__main__":
    runner = LLMRingRunner()
    runner.run()