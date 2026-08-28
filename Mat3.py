import math
import random
import re
import json
import os
import sys
import zlib
import struct
from datetime import datetime

GRAMMEE_FILE = "correct_grammee.json"

def load_grammee_db():
    if os.path.exists(GRAMMEE_FILE):
        with open(GRAMMEE_FILE, "r", encoding="utf-8") as f:
            try: 
                return json.load(f)
            except Exception: 
                pass
    return {
        "valid_transitions": {
            "i": ["am", "have", "want", "like", "do"],
            "you": ["are", "have", "want", "do", "like"],
            "how": ["are", "is", "do"],
            "what": ["is", "are", "do", "happened"],
            "the": ["cat", "dog", "code", "system", "user"]
        },
        "bad_patterns": []
    }

def save_grammee_db(db):
    with open(GRAMMEE_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)


class ImageGeneratorEngine:
    
    COLOR_MAP = {
        'r': (255, 0, 0),
        'g': (0, 255, 0),
        'b': (0, 0, 255),
        'y': (255, 255, 0),
        'c': (0, 255, 255),
        'm': (255, 0, 255),
        'w': (255, 255, 255),
        'k': (0, 0, 0),
        'o': (255, 165, 0), 
        'p': (255, 192, 203),
        'd': (128, 128, 128),
        'l': (211, 211, 211),
        '1': (100, 50, 0),
        '2': (50, 150, 50),
        '3': (150, 50, 100),
    }
    
    def text_to_numbers(self, text, mode="2num"):
        num1 = sum(ord(c) for c in text.lower())
        num2 = len(text) * sum(i * ord(c) for i, c in enumerate(text.lower()))
        
        if mode == "2num":
            return [num1, num2]
        else:
            num3 = sum((ord(c) ** 2) for c in text.lower()) % 10000
            num4 = len(text) * len(set(text.lower()))
            return [num1, num2, num3, num4]
    
    def text_to_image_representation(self, text, width=50, height=30):
        lines = []
        text_lower = text.lower()
        
        for y in range(height):
            line = ""
            for x in range(width):
                text_idx = (y * width + x) // max(1, (width * height // len(text_lower)))
                
                if text_idx < len(text_lower):
                    char = text_lower[text_idx]
                    if char.isalpha():
                        line += 'w'
                    elif char.isdigit():
                        line += 'y'
                    else:
                        line += 'c'
                else:
                    line += 'k'
            lines.append(line)
        
        return '\n'.join(lines)
    
    def corrupt_pattern(self, text_data, remove_percent=0.30, rng=None):
        if rng is None:
            rng = random.Random()
        
        lines = text_data.split('\n')
        corrupted_lines = []
        
        for line in lines:
            corrupted_line = ""
            for char in line:
                if rng.random() < remove_percent:
                    corrupted_line += rng.choice(list(self.COLOR_MAP.keys()))
                else:
                    corrupted_line += char
            corrupted_lines.append(corrupted_line)
        
        return '\n'.join(corrupted_lines)
    
    def create_advanced_math_pattern(self, text, width=50, height=30):
        mode = random.choice(["2num", "4num"])
        numbers = self.text_to_numbers(text, mode)
        start = random.randint(1000000, 9999999)
        
        if mode == "2num":
            num1, num2 = numbers
            final_seed = start * num2
        else:
            num1, num2, num3, num4 = numbers
            final_seed = start * num2 * num3 * num4
        
        rng = random.Random(final_seed)
        text_image = self.text_to_image_representation(text, width, height)
        corrupted_image = self.corrupt_pattern(text_image, remove_percent=0.30, rng=rng)
        mat_image = self.apply_idk_effect(corrupted_image, intensity=0.25, rng=rng)
        
        self.last_generation_data = {
            "text": text,
            "mode": mode,
            "start": start,
            "numbers": numbers,
            "final_seed": final_seed,
            "num_count": len(numbers)
        }
        
        return mat_image
    
    def apply_idk_effect(self, text_data, intensity=0.3, rng=None):
        if rng is None:
            rng = random.Random()
        
        lines = text_data.split('\n')
        img_lines = []
        
        for i, line in enumerate(lines):
            img_line = ""
            for j, char in enumerate(line):
                if char not in self.COLOR_MAP:
                    img_line += char
                    continue
                
                if rng.random() < intensity * 0.2:
                    img_line += char * rng.randint(2, 4)
                elif rng.random() < intensity * 0.1:
                    img_line += rng.choice(list(self.COLOR_MAP.keys()))
                else:
                    img_line += char
            img_lines.append(img_line)
        
        final_lines = []
        for line in img_lines:
            final_lines.append(line)
            if rng.random() < intensity * 0.15:
                final_lines.append(line)
        
        return '\n'.join(final_lines)
    
    def text_to_png(self, text_data, pixel_size=16, output_path="output.png"):
        lines = text_data.split('\n')
        lines = [l for l in lines if l.strip()]
        
        width = max(len(line) for line in lines) if lines else 10
        height = len(lines)
        
        img_width = width * pixel_size
        img_height = height * pixel_size
        
        raw_data = bytearray()
        
        for y in range(img_height):
            raw_data.append(0)
            for x in range(img_width):
                text_x = x // pixel_size
                text_y = y // pixel_size
                
                if text_y < len(lines) and text_x < len(lines[text_y]):
                    char = lines[text_y][text_x]
                    if char in self.COLOR_MAP:
                        r, g, b = self.COLOR_MAP[char]
                    else:
                        r, g, b = 0, 0, 0
                else:
                    r, g, b = 0, 0, 0
                
                raw_data.extend([r, g, b])
        
        compressed = zlib.compress(bytes(raw_data))
        
        png_data = bytearray()
        png_data.extend(b'\x89PNG\r\n\x1a\n')
        
        ihdr_data = struct.pack('>IIBBBBB', img_width, img_height, 8, 2, 0, 0, 0)
        png_data.extend(struct.pack('>I', 13))
        png_data.extend(b'IHDR')
        png_data.extend(ihdr_data)
        crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        png_data.extend(struct.pack('>I', crc))
        
        png_data.extend(struct.pack('>I', len(compressed)))
        png_data.extend(b'IDAT')
        png_data.extend(compressed)
        crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        png_data.extend(struct.pack('>I', crc))
        
        png_data.extend(struct.pack('>I', 0))
        png_data.extend(b'IEND')
        crc = zlib.crc32(b'IEND') & 0xffffffff
        png_data.extend(struct.pack('>I', crc))
        
        with open(output_path, 'wb') as f:
            f.write(png_data)
        
        return output_path
    
    def generate(self, user_text=""):
        text_data = self.create_advanced_math_pattern(user_text)
        filename = f"matimg_{int(datetime.now().timestamp() * 1000)}.png"
        self.text_to_png(text_data, 16, filename)
        return filename, self.last_generation_data


class AdaptiveMatrixCore:
    def __init__(self, database):
        self.database = database
        self.intents = database.get("intents", [])
        self.restart_count = database.get("restart_count", 0)
        self.tags = sorted([intent["tag"] for intent in self.intents])
        
        self.nn_vocab = set()
        for intent in self.intents:
            for pattern in intent.get("patterns", []):
                self.nn_vocab.update(re.findall(r'\w+', pattern.lower()))
        self.nn_vocab = sorted(list(self.nn_vocab))
        
        input_dim = len(self.nn_vocab)
        hidden_dim = 16
        output_dim = len(self.tags)
        
        bound1 = math.sqrt(6.0 / (input_dim + hidden_dim)) if (input_dim + hidden_dim) > 0 else 0.1
        self.W1 = [[random.uniform(-bound1, bound1) for _ in range(hidden_dim)] for _ in range(input_dim)]
        self.b1 = [0.0] * hidden_dim
        bound2 = math.sqrt(6.0 / (hidden_dim + output_dim)) if (hidden_dim + output_dim) > 0 else 0.1
        self.W2 = [[random.uniform(-bound2, bound2) for _ in range(output_dim)] for _ in range(hidden_dim)]
        self.b2 = [0.0] * output_dim
        
        self.computed_epochs = 300 + (self.restart_count * 50)
        if self.computed_epochs > 1500: 
            self.computed_epochs = 1500
        
        self.image_gen = ImageGeneratorEngine()
        
        self.train_all_engines()

    def engine_one_math(self, expression):
        clean = re.sub(r'[^0-9.+\-*/() ]', '', expression)
        if not clean.strip() or not any(op in clean for op in ['+', '-', '*', '/']): 
            return None
        try:
            result = eval(clean, {"__builtins__": None}, {})
            return int(result) if float(result).is_integer() else float(result)
        except Exception:
            return None

    def train_all_engines(self):
        print(f"[Mat]: Launching (ligma and btw mat stands for nothing)")
        print(f"[Mat]: Restart count or shit idfk: #{self.restart_count}. Training shit: {self.computed_epochs}")
        
        training_data = []
        for intent in self.intents:
            tag_idx = self.tags.index(intent["tag"])
            target = [0.0] * len(self.tags)
            target[tag_idx] = 1.0
            for pattern in intent.get("patterns", []):
                tokens = re.findall(r'\w+', pattern.lower())
                vector = [1.0 if word in tokens else 0.0 for word in self.nn_vocab]
                training_data.append((vector, target))

        for epoch in range(self.computed_epochs):
            if epoch % 200 == 0 and epoch > 0:
                print(f" -> Tensor processing gotta sweep sweep sweep yes im talking about baldis basics: {epoch}/{self.computed_epochs} ")
                
            for X, y_true in training_data:
                z1 = [sum(X[i] * self.W1[i][j] for i in range(len(X))) + self.b1[j] for j in range(len(self.b1))]
                a1 = [max(0.0, x) for x in z1]
                z2 = [sum(a1[i] * self.W2[i][j] for i in range(len(a1))) + self.b2[j] for j in range(len(self.b2))]
                
                max_val = max(z2) if z2 else 0.0
                exp_vals = [math.exp(x - max_val) for x in z2]
                sum_exp = sum(exp_vals) if sum(exp_vals) > 0 else 1.0
                a2 = [x / sum_exp for x in exp_vals]
                
                loss_grad_z2 = [y_hat - y for y_hat, y in zip(a2, y_true)]
                dW2 = [[a1[i] * loss_grad_z2[j] for j in range(len(self.b2))] for i in range(len(a1))]
                loss_grad_a1 = [sum(loss_grad_z2[j] * self.W2[i][j] for j in range(len(self.b2))) for i in range(len(a1))]
                loss_grad_z1 = [grad if val > 0 else 0.0 for val, grad in zip(z1, loss_grad_a1)]
                dW1 = [[X[i] * loss_grad_z1[j] for j in range(len(self.b1))] for i in range(len(X))]
                
                for i in range(len(self.W1)):
                    for j in range(len(self.W1[0])): self.W1[i][j] -= 0.1 * dW1[i][j]
                for j in range(len(self.b1)): self.b1[j] -= 0.1 * loss_grad_z1[j]
                for i in range(len(self.W2)):
                    for j in range(len(self.W2[0])): self.W2[i][j] -= 0.1 * dW2[i][j]
                for j in range(len(self.b2)): self.b2[j] -= 0.1 * loss_grad_z2[j]
        print("[Mat]: Sync mat finally successfully has done it fucking shit.\n")

    def engine_two_classify(self, user_tokens):
        X = [1.0 if word in user_tokens else 0.0 for word in self.nn_vocab]
        z1 = [sum(X[i] * self.W1[i][j] for i in range(len(X))) + self.b1[j] for j in range(len(self.b1))]
        a1 = [max(0.0, x) for x in z1]
        z2 = [sum(a1[i] * self.W2[i][j] for i in range(len(a1))) + self.b2[j] for j in range(len(self.b2))]
        
        max_val = max(z2) if z2 else 0.0
        exp_vals = [math.exp(x - max_val) for x in z2]
        sum_exp = sum(exp_vals) if sum(exp_vals) > 0 else 1.0
        a2 = [x / sum_exp for x in exp_vals]
        
        matched_tags = [self.tags[i] for i, prob in enumerate(a2) if prob > 0.50]
        
        if not matched_tags:
            matched_tags = [self.tags[a2.index(max(a2))]]
            
        return matched_tags[0] if isinstance(matched_tags, list) else matched_tags

    def engine_three_mrkv(self, user_tokens, matched_tag):
        transitions = {}
        for intent in self.intents:
            if intent["tag"] == matched_tag and "transitions" in intent:
                transitions.update(intent["transitions"])
                    
        if not transitions:
            for intent in self.intents:
                if "transitions" in intent:
                    transitions.update(intent["transitions"])

        if not transitions:
            return "I am shitzing.", []

        curr_sequence = ["<START>"]
        generated_words = []
        
        for _ in range(20):
            next_word = None
            for order in range(min(4, len(curr_sequence)), 0, -1):
                ctx_key = " ".join(curr_sequence[-order:])
                if ctx_key in transitions and transitions[ctx_key]:
                    candidates = transitions[ctx_key]
                    words = list(candidates.keys())
                    weights = list(candidates.values())
                    next_word = random.choices(words, weights=weights, k=1)[0]
                    break
                    
            if not next_word or next_word == "<END>": 
                break
            generated_words.append(next_word)
            curr_sequence.append(next_word)
            
        if not generated_words:
            return "I shit u not i didnt gen any words in this msg.", []
            
        res = " ".join(generated_words)
        combined_base = res[0].upper() + res[1:]
        return combined_base, generated_words

    def engine_four_generate(self, base_phrase, alternate_phrases):

        grammee_db = load_grammee_db()
        current_context = re.findall(r'\w+', base_phrase.lower())
        if not current_context:
            current_context = ["i", "am"]

        best_sentence = base_phrase
        max_attempts = 5

        for attempt in range(max_attempts):
 
            x_a = [1.0 if w in current_context else 0.0 for w in self.nn_vocab]
            h1_a = [max(0.0, sum(x_a[i] * self.W1[i][j] for i in range(len(x_a))) + self.b1[j]) for j in range(len(self.b1))]
            out_a = [sum(h1_a[i] * self.W2[i][j] for i in range(len(h1_a))) + self.b2[j] for j in range(len(self.tags))]

            top_tag_idx = out_a.index(max(out_a)) if out_a else 0

            x_b = [1.0 if i == top_tag_idx else 0.0 for i in range(len(self.tags))]
            h1_b = [max(0.0, sum(x_b[i] * self.W2[j % len(x_b)][i] for i in range(len(x_b)))) for j in range(len(self.b1))]

            draft_tokens = current_context.copy()
            if isinstance(alternate_phrases, list) and alternate_phrases:
                for word in alternate_phrases:
                    if word not in ["<START>", "<END>"] and word not in draft_tokens:
                        draft_tokens.append(word)

            candidate_phrase = " ".join(draft_tokens)

            is_valid, natural_score, feedback = self.engine_five_grammar(candidate_phrase, grammee_db)

            if is_valid and natural_score >= 0.70:
                best_sentence = candidate_phrase
                break
            else:
                suggested = feedback.get("suggested_words", [])
                bad_pair = feedback.get("bad_pair", None)

                if bad_pair and bad_pair not in grammee_db["bad_patterns"]:
                    grammee_db["bad_patterns"].append(bad_pair)

                if suggested:
                    current_context.append(random.choice(suggested))
                else:
                    current_context = current_context[:1]

                best_sentence = candidate_phrase

        save_grammee_db(grammee_db)
        
        out = re.sub(r"\s+([.,!?:])", r"\1", best_sentence).strip()
        return out.capitalize() + "." if out else "I am here."

    def engine_five_grammar(self, phrase, grammee_db):

        words = re.findall(r'\w+', phrase.lower())
        if len(words) < 2:
            return True, 1.0, {"status": "ok"}

        valid_map = grammee_db.get("valid_transitions", {})
        bad_patterns = grammee_db.get("bad_patterns", [])

        total_pairs = len(words) - 1
        abnormal_count = 0
        suggested_replacements = []

        for i in range(total_pairs):
            w1, w2 = words[i], words[i+1]
            pair_str = f"{w1} {w2}"

            if pair_str in bad_patterns:
                abnormal_count += 1
                continue

            if w1 in valid_map:
                allowed_next = valid_map[w1]
                if w2 not in allowed_next:
                    abnormal_count += 1
                    suggested_replacements.extend(allowed_next)
            else:
                plausible_next = [v for v in self.nn_vocab if len(v) > 2][:3]
                valid_map[w1] = plausible_next
                suggested_replacements.extend(plausible_next)

        abnormal_rate = abnormal_count / max(1, total_pairs)
        natural_score = 1.0 - abnormal_rate

        if abnormal_rate > 0.30:
            return False, natural_score, {
                "status": "re_try",
                "abnormal_rate": abnormal_rate,
                "suggested_words": list(set(suggested_replacements)),
                "bad_pair": f"{words[0]} {words[1]}" if len(words) >= 2 else None
            }

        return True, natural_score, {"status": "ok", "suggested_words": []}

    def learn_from_user(self, user_input, ai_response, matched_tag):
        for intent in self.intents:
            if intent["tag"] == matched_tag:
                intent["corpus"] += f" {user_input} {ai_response}"
                
                user_tokens = re.findall(r'\w+', user_input.lower())
                resp_tokens = re.findall(r'\w+', ai_response.lower())
                
                if user_input.lower() not in intent.get("patterns", []) and len(user_tokens) < 4:
                    intent.setdefault("patterns", []).append(user_input.lower())
                
                transitions = intent.setdefault("transitions", {})
                
                u_path = ["<START>"] + user_tokens + ["<END>"]
                for i in range(len(u_path) - 1):
                    anchor = u_path[i]
                    target = u_path[i + 1]
                    if anchor not in transitions:
                        transitions[anchor] = {}
                    transitions[anchor][target] = transitions[anchor].get(target, 0) + 2

                r_path = ["<START>"] + resp_tokens + ["<END>"]
                for depth in range(1, 5):
                    for i in range(len(r_path) - depth):
                        ctx_key = " ".join(r_path[i : i + depth])
                        target_word = r_path[i + depth]
                        if ctx_key not in transitions:
                            transitions[ctx_key] = {}
                        transitions[ctx_key][target_word] = transitions[ctx_key].get(target_word, 0) + 1
        
        self.database["intents"] = self.intents
        with open("ai_train.json", "w", encoding="utf-8") as f:
            json.dump(self.database, f, indent=4)


class SessionStorageController:
    def __init__(self, filename="chats.json"):
        self.filename = filename
        self.sessions = self.load_sessions()
        self.current_session_id = None
        
        if not self.sessions:
            self.create_new_session("Initial Chat Session")
        else:
            self.current_session_id = list(self.sessions.keys())[-1]

    def load_sessions(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                try: return json.load(f)
                except Exception: return {}
        return {}

    def save_sessions(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.sessions, f, indent=4)

    def create_new_session(self, title=None):
        self.current_session_id = str(int(datetime.now().timestamp() * 1000))
        if not title:
            title = f"Chat Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.sessions[self.current_session_id] = {
            "title": title,
            "created_at": datetime.now().isoformat(),
            "history": []
        }
        self.save_sessions()
        print(f"[Session Subprocessor]: New something chat time done idk: '{title}'")

    def append_message(self, role, message, meta=None):
        if self.current_session_id in self.sessions:
            self.sessions[self.current_session_id]["history"].append({
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": message,
                "meta": meta if meta else {}
            })
            self.save_sessions()

    def list_all_sessions(self):
        print("\n==================================================")
        print("          THE FUCKING SHITZING CHATS           ")
        print("==================================================")
        ids = list(self.sessions.keys())
        for idx, s_id in enumerate(ids):
            title = self.sessions[s_id]["title"]
            msg_count = len(self.sessions[s_id]["history"])
            marker = ">>> ACTIVE <<<" if s_id == self.current_session_id else ""
            print(f" [{idx}] {title} ({msg_count} interactions) {marker}")
        print("==================================================")
        return ids

    def switch_to_session(self, idx, session_ids):
        if 0 <= idx < len(session_ids):
            self.current_session_id = session_ids[idx]
            print(f"\n[Session Subprocessor]: USER wanted to fuck to a dif chat for user shit idk: '{self.sessions[self.current_session_id]['title']}'")
            print("--------------------------------------------------")
            for chat in self.sessions[self.current_session_id]["history"]:
                speaker = "You" if chat["role"] == "user" else "mat"
                print(f"{speaker} > {chat['content']}")
            print("--------------------------------------------------")
        else:
            print("[Session Error]: Vector index boundary violation. Action canceled.")


DEFAULT_TRAIN_DATA = {
    "restart_count": 0,
    "intents": [
        {
            "tag": "words",
            "patterns": [
                "hru",
                "what",
                "4\u00d73",
                "# =====================================================================",
                "cya",
                "wait fr",
                "yeah",
                "ok bye",
                "hey mat"
            ],
            "corpus": "How are you holding up out there? Always ready to calculate some formulas or chat about something interesting.",
            "transitions": {
                "<START>": {"i": 2, "how": 2},
                "how": {"smart": 2, "are": 2},
                "smart": {"are": 2},
                "are": {"you": 4},
                "you": {"holding": 2, "doing": 2, "<END>": 2},
                "holding": {"up": 2},
                "up": {"out": 2},
                "out": {"there": 2},
                "there": {"<END>": 2}
            }
        },        
        {
            "tag": "greeting",
            "patterns": ["hi", "hello", "yo", "hey", "whats up", "hru", "how are you", "what"],
            "corpus": "Yo! What is up human? Hello there!",
            "transitions": {
                "<START>": {"yo": 3, "hello": 2, "i": 2},
                "yo": {"what": 2, "there": 1, "<END>": 1},
                "what": {"is": 2, "up": 2},
                "is": {"up": 2},
                "up": {"human": 1, "there": 1, "<END>": 2},
                "hello": {"there": 2},
                "there": {"i": 1, "<END>": 2},
                "i": {"am": 2},
                "am": {"doing": 2, "great": 1},
                "doing": {"great": 2, "well": 1},
                "great": {"inside": 1, "today": 1, "<END>": 2}
            }
        },
        {
            "tag": "royalty",
            "patterns": ["king", "queen", "palace", "crown", "monarch", "empire"],
            "corpus": "The royal bloodline guards the castle palace gates securely."
        },
        {
            "tag": "swears",
            "patterns": [
                "fuck",
                "bitch",
                "dumbass",
                "shit",
                "whore",
                "fucker",
                "cunt",
                "idiot",
                "fuck you"
            ],
            "corpus": "fuck you too. oh you shitting me rn well fuck off bitch.",
            "transitions": {
                "<START>": {"fuck": 4, "oh": 1, "your": 1},
                "fuck": {"you": 3, "off": 1},
                "you": {"too": 2, "bitch": 1, "<END>": 2},
                "oh": {"you": 1},
                "off": {"bitch": 1},
                "bitch": {"<END>": 2}
            }
        },
        {
            "tag": "image_generation",
            "patterns": ["gen", "make", "create", "generate", "draw", "image", "picture", "art"],
            "corpus": ""
        },        
        {
            "tag": "ballistics",
            "patterns": ["gun", "shot", "weapon", "bullet", "firing", "trigger"],
            "corpus": "Ballistic trajectories map the precise velocity vectors of projectiles."
        }
    ]
}

if os.path.exists("ai_train.json"):
    with open("ai_train.json", "r", encoding="utf-8") as f:
        try: 
            master_train_db = json.load(f)
            master_train_db["restart_count"] += 1
        except Exception:
            master_train_db = DEFAULT_TRAIN_DATA
else:
    master_train_db = DEFAULT_TRAIN_DATA

with open("ai_train.json", "w", encoding="utf-8") as f:
    json.dump(master_train_db, f, indent=4)

AI_Core = AdaptiveMatrixCore(master_train_db)
Chat_Manager = SessionStorageController()

print("==================================================")
print("     CHAT MAT    ")
print("==================================================")
print("[Controls]: Type gen to make it gen images")
print("[Controls]: Type /nc to shit a new chating folder.")
print("[Controls]: Type /c to shit and choose chats.")
print("[Controls]: Type /thoughts to see mat's reasoning.\n")

while True:
    try:
        user_input = input("You > ").strip()
        if not user_input: continue
        if user_input.lower() == 'exit': break

        if user_input.lower() == '/nc':
            title_input = input("Enter Chat Title (or press enter for default lazy dumbass): ").strip()
            Chat_Manager.create_new_session(title_input if title_input else None)
            print()
            continue

        if user_input.lower() == '/c':
            available_ids = Chat_Manager.list_all_sessions()
            try:
                choice = int(input("Select session index: ").strip())
                Chat_Manager.switch_to_session(choice, available_ids)
            except (ValueError, IndexError):
                print("[Error]: Invalid index.")
            print()
            continue

        if user_input.lower() == '/thoughts':
            history = Chat_Manager.sessions[Chat_Manager.current_session_id]["history"]
            if len(history) < 2:
                print("mat > [Thoughts]: No previous message to recall.\n")
                continue
            
            last_ai_msg = None
            for msg in reversed(history):
                if msg["role"] == "ai":
                    last_ai_msg = msg
                    break
            
            if not last_ai_msg:
                print("mat > [Thoughts]: No previous AI message found.\n")
                continue
            
            metadata = last_ai_msg.get("meta", last_ai_msg.get("metadata", {}))
            thoughts = f"[Thoughts from previous message]:\n"
            thoughts += f"  Engine: {metadata.get('engine', 'unknown')}\n"
            
            if metadata.get('engine') == 4:
                thoughts += f"  Classification: {metadata.get('classification', 'unknown')}\n"
                thoughts += f"  Base Pattern: {metadata.get('base_pattern', 'N/A')}\n"
                thoughts += f"  Alt Pattern: {metadata.get('alt_pattern', 'N/A')}\n"
            elif metadata.get('engine') == 1:
                thoughts += f"  Math Calculation: {metadata.get('calculation', 'N/A')}\n"
            elif metadata.get('engine') == 'image_gen':
                thoughts += f"  Image Type: {metadata.get('type', 'N/A')}\n"
                thoughts += f"  File: {metadata.get('file', 'N/A')}\n"
                thoughts += f"  Mode: {metadata.get('math_data', {}).get('mode', 'N/A')}\n"
                thoughts += f"  Seed: {metadata.get('math_data', {}).get('final_seed', 'N/A')}\n"
            
            print(f"mat > {thoughts}\n")
            continue

        if any(kw in user_input for kw in ['import ', 'def ', 'class ', 'return ', ' = ']) or len(user_input) > 250:
            print("mat > [Input Rejected]: Injection detected.\n")
            continue

        math_res = AI_Core.engine_one_math(user_input)
        if math_res is not None:
            output_msg = f"[Math Result]: {math_res}"
            print(f"mat > {output_msg}\n")
            Chat_Manager.append_message("user", user_input)
            Chat_Manager.append_message("ai", output_msg, {"engine": 1, "type": "calculation"})
            continue

        image_keywords = ['gen', 'make', 'create', 'generate', 'draw', 'image', 'picture']
        if any(kw in user_input.lower() for kw in image_keywords):
            print("mat > [Image Engine Activated] Generating image...")
            try:
                filename, gen_data = AI_Core.image_gen.generate(user_input)
                
                mode_desc = f"{gen_data['num_count']}-number mode"
                output_msg = f"[Image Generated]: {filename}\n"
                output_msg += f"    Request: '{gen_data['text']}'\n"
                output_msg += f"    Mode: {mode_desc}\n"
                output_msg += f"    Start: {gen_data['start']} (random)\n"
                output_msg += f"    Numbers: {gen_data['numbers']}\n"
                output_msg += f"    Final Seed: {gen_data['final_seed']}\n"
                output_msg += f"    Process: text→image → 30% corrupted → noise → idk effects → PNG"
                
                print(f"mat > {output_msg}\n")
                Chat_Manager.append_message("user", user_input)
                Chat_Manager.append_message("ai", output_msg, {
                    "engine": "image_gen", 
                    "type": "image", 
                    "file": filename,
                    "math_data": gen_data
                })
                continue
            except Exception as e:
                output_msg = f"[Image Error]: Could not generate image - {str(e)}"
                print(f"mat > {output_msg}\n")
                Chat_Manager.append_message("user", user_input)
                Chat_Manager.append_message("ai", output_msg, {"engine": "image_gen", "type": "error"})
                continue

        Chat_Manager.append_message("user", user_input)
        user_tokens = re.findall(r'\w+', user_input.lower())

        matched_tag = AI_Core.engine_two_classify(user_tokens)

        base_p, alt_p = AI_Core.engine_three_mrkv(user_tokens, matched_tag)

        final_output = AI_Core.engine_four_generate(base_p, alt_p)
        print(f"mat > {final_output}\n")

        Chat_Manager.append_message("ai", final_output, {
            "engine": 4, 
            "classification": matched_tag,
            "base_pattern": str(base_p)[:100],
            "alt_pattern": str(alt_p)[:100]
        })

        AI_Core.learn_from_user(user_input, final_output, matched_tag)

    except (KeyboardInterrupt, EOFError):
        print("\n[System]: Shutting down. Goodbye!")
        sys.exit(0)
