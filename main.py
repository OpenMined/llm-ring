import os
import json
from glob import glob
from transformers import AutoTokenizer, AutoModelForCausalLM
from syftbox.lib import ClientConfig
from pathlib import Path


class RingRunner:
    def __init__(self):
        # config_path = os.environ.get("SYFTBOX_CLIENT_CONFIG_PATH", None)
        client_config = ClientConfig.load(
            os.path.expanduser("~/.syftbox/client_config.json")
        )
        self.my_email = client_config["email"]
        self.my_home = (
            Path(os.path.abspath(__file__)).parent.parent.parent
            / self.my_email
            / "app_pipelines"
            / "llm_ring"
        )
        self.app_path = (
            Path(os.path.abspath(__file__)).parent.parent.parent / "apps" / "llm_ring"
        )

        self.input_folder = self.my_home / "input"
        self.running_folder = self.my_home / "running"
        self.done_folder = self.my_home / "done"
        self.folders = [self.input_folder, self.running_folder, self.done_folder]

    def setup_folders(self):
        print("Setting up the necessary folders.")

        for folder in self.folders:
            os.makedirs(folder, exist_ok=True)
            with open(folder / "dummy", "w") as f:
                pass

    def check_datafile_exists(self):
        files = []
        for file in os.listdir(self.running_folder):
            if file.endswith(".json"):
                files.append(os.path.join(self.running_folder, file))
        print(f"Found {len(files)} files.")
        return files

    def call_llm(self, query, data):
        prompt = f"""Please answer the following question: {query}
        Use the following information to answer the query:
        {data}
         ONLY ANSWER TRUE OR FALSE. DO NOT INCLUDE ANY OTHER TEXT.
        """
        print("Prompt used: ", prompt)

        from transformers import pipeline

        messages = [
            {"role": "user", "content": prompt},
        ]

        pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        prompt = pipe.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        outputs = pipe(
            prompt,
            max_new_tokens=1,
            do_sample=False,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
        )
        print(outputs[0]["generated_text"])
        breakpoint()
        # return result[0][-1]["content"]

    def data_read_and_increment(self, file_name):
        with open(file_name) as f:
            data = json.load(f)

        ring_participants = data["ring"]
        datum = data["data"]
        to_send_idx = data["current_index"] + 1

        if to_send_idx >= len(ring_participants):
            print("END TRANSMISSION.")
            to_send_email = None
        else:
            to_send_email = ring_participants[to_send_idx]

        # processing
        with open(f"{self.app_path}/secrets.txt") as f:
            secrets = f.readlines()

        result = self.call_llm(data["query"], secrets)
        if "true" in result.lower():
            data["data"] = datum + 1

        data["current_index"] = to_send_idx
        os.remove(file_name)
        return data, to_send_email

    def data_writer(self, file_name, result):
        with open(file_name, "w") as f:
            json.dump(result, f)

    def send_to_new_person(self, to_send_email, datum):
        output_path = (
            Path(os.path.abspath(__file__)).parent.parent.parent
            / to_send_email
            / "app_pipelines"
            / "llm_ring"
            / "running"
            / "data.json"
        )
        self.data_writer(output_path, datum)

    def terminate_ring(self):
        my_ring_runner.data_writer(self.done_folder / "data.json", datum)


if __name__ == "__main__":
    # Start of script. Step 1. Setup any folders that may be necessary.
    my_ring_runner = RingRunner()
    my_ring_runner.setup_folders()
    # Step 2. Check if you have received a data file in your input folder.
    file_names = my_ring_runner.check_datafile_exists()
    # Step 3. If you have found a data file, proceed. Else, nothing.
    if len(file_names) > 0:
        print("Found a data file! Let's go to work.")
        # For this example, this will always be 1. But we can in theory do more complicated logic.
        for file_name in file_names:
            # Step 4. Read the data_file, increment the number and send it to the next person.
            datum, to_send_email = my_ring_runner.data_read_and_increment(file_name)
            # Step 5. If there is another person in the ring, send it to them. Else, terminate.
            if to_send_email:
                my_ring_runner.send_to_new_person(to_send_email, datum)
            else:
                my_ring_runner.terminate_ring()
    else:
        print("No data file found. As you were, soldier.")
