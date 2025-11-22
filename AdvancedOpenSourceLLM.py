import re
import json
import os
import string
from collections import defaultdict, Counter


import sys
import io

# Enable UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

###############################################################################
# CORE LLM CLASS
###############################################################################

class ExpertFieldLLM:
    def __init__(self):
        ########## INITIALIZATION ##########
        self.word_db = defaultdict(dict)
        self.word_relationships = defaultdict(lambda: defaultdict(float))
        self.pattern_relationships = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        self.mode = 'formal'
        self.operation_mode = 'speech'
        self.grammar_rules = {}
        self._min_words = 7
        self._max_words = 100
        
        @property
        def min_words(self):
            return self._min_words
        
        @min_words.setter
        def min_words(self, value):
            """Validate and set minimum words"""
            value = max(1, min(value, 50))  # Limit between 1 and 50
            if value > self._max_words:
                self._max_words = value + 5  # Auto-adjust max if needed
            self._min_words = value
        
        @property
        def max_words(self):
            return self._max_words
        
        @max_words.setter
        def max_words(self, value):
            """Validate and set maximum words"""
            value = max(5, min(value, 100))  # Limit between 5 and 100
            if value < self._min_words:
                self._min_words = max(1, value - 5)  # Auto-adjust min if needed
            self._max_words = value
        
        ########## CONFIGURATION FILES ##########
        self.config_files = {
            'question_words': 'question_words.txt',
            'answer_words': 'answer_words.txt', 
            'fact_words': 'fact_words.txt',
            'theory_words': 'theory_words.txt',
            'past_indicators': 'past_indicators.txt',
            'future_indicators': 'future_indicators.txt',
            'grammar_flow_formal': 'grammar_flow_formal.json',
            'grammar_flow_casual': 'grammar_flow_casual.json',
            'dictionary_data': 'dictionary_data.txt',
            'plural_rules': 'plural_rules.json',
            'expert_fields': 'expert_fields.json',
            'python_syntax': 'python_syntax.json',
            'code_snippets': 'code_snippets.json'
        }
        
        ########## ENHANCEMENT SETTINGS ##########
        self.min_words = 3
        self.max_words = 20
        self.internet_enabled = False
        self.code_enabled = False
        self.image_enabled = False
        self.ascii_enabled = False
        
        ########## EXECUTION ORDER ##########
        self._ensure_files_exist()           # STEP 1: Create files
        self.load_config_files()             # STEP 2: Load configs
        self.import_dictionary()             # STEP 3: Import dictionary
        self._initialize_enhancements()      # STEP 4: Initialize enhancements

    ###############################################################################
    # FILE MANAGEMENT
    ###############################################################################

    def _ensure_files_exist(self):
        """Create all necessary files if they don't exist"""
        ########## WORD LIST FILES ##########
        word_files = {
            'question_words.txt': ['?', 'what', 'when', 'where', 'why', 'how', 'which', 'who'],
            'answer_words.txt': ['because', 'therefore', 'thus', 'so', 'hence'],
            'fact_words.txt': ['fact', 'actually', 'proven', 'evidence', 'study', 'research'],
            'theory_words.txt': ['theory', 'hypothesis', 'maybe', 'perhaps', 'possibly', 'could'],
            'past_indicators.txt': ['ed', 'was', 'were', 'had', 'did', 'been'],
            'future_indicators.txt': ['will', 'shall', 'going to', 'gonna', 'about to']
        }
        
        for filename, words in word_files.items():
            if not os.path.exists(filename):
                with open(filename, 'w') as f:
                    for word in words:
                        f.write(word + '\n')

        ########## PLURAL RULES ##########
        plural_rules = {
            "regular_rules": {
                "s": ["s", "x", "z", "ch", "sh"],
                "es": ["s", "x", "z", "ch", "sh"],
                "ies": ["y"],
                "ves": ["f", "fe"]
            },
            "irregular_rules": {
                "man": "men", "woman": "women", "child": "children",
                "person": "people", "foot": "feet", "tooth": "teeth"
            },
            "unchanged_words": ["sheep", "deer", "fish", "species", "aircraft"]
        }
        
        if not os.path.exists('plural_rules.json'):
            with open('plural_rules.json', 'w') as f:
                json.dump(plural_rules, f, indent=2)

        ########## EXPERT FIELDS ##########
        expert_fields = {
            "stem": {"weight": 1.5, "keywords": ["science", "technology", "engineering", "math", "physics", "chemistry"]},
            "art": {"weight": 1.3, "keywords": ["paint", "draw", "design", "creative", "color", "artist"]},
            "music": {"weight": 1.3, "keywords": ["song", "music", "sound", "instrument", "melody", "rhythm"]},
            "strategy": {"weight": 1.4, "keywords": ["plan", "strategy", "tactic", "game", "win", "compete"]},
            "news": {"weight": 1.2, "keywords": ["news", "current", "event", "today", "update", "trending"]},
            "programming": {"weight": 1.6, "keywords": ["code", "program", "software", "algorithm", "function", "variable"]}
        }
        
        if not os.path.exists('expert_fields.json'):
            with open('expert_fields.json', 'w') as f:
                json.dump(expert_fields, f, indent=2)

        ########## GRAMMAR RULES ##########
        default_grammar = {
            "common_pairs": {
                "noun": ["verb", "adjective"], "verb": ["noun", "adverb"],
                "adjective": ["noun"], "adverb": ["verb", "adjective"]
            },
            "compatibility_rules": {
                "noun": {"verb": 0.8, "adjective": 0.6},
                "verb": {"noun": 0.8, "adverb": 0.7},
                "adjective": {"noun": 0.9}, "adverb": {"verb": 0.8}
            },
            "flow_rules": {
                "noun": {"verb": 0.9}, "verb": {"noun": 0.8},
                "adjective": {"noun": 0.9}, "adverb": {"verb": 0.8}
            },
            "sentence_order": {
                "statement": ["noun", "verb", "noun"],
                "question": ["question_word", "verb", "noun"],
                "command": ["verb", "noun"]
            }
        }
        
        if not os.path.exists('grammar_flow_formal.json'):
            with open('grammar_flow_formal.json', 'w') as f:
                json.dump(default_grammar, f, indent=2)
        
        if not os.path.exists('grammar_flow_casual.json'):
            with open('grammar_flow_casual.json', 'w') as f:
                json.dump({}, f, indent=2)

        ########## DICTIONARY DATA ##########
        if not os.path.exists('dictionary_data.txt'):
            sample_data = [
                "noun; computer; computer; computers; machine,device,pc; ; electronic device; PC,CPU; {}",
                "verb; compute; compute; computes; calculate,process,analyze; ; perform calculations; ; {}",
                "noun; data; datum; data; information,facts,stats; ; collected information; ; {}",
                "verb; analyze; analyze; analyzes; examine,study,process; ignore,skip; examine methodically; ; {}",
                "adjective; digital; digital; ; electronic,computerized; analog; relating to computers; ; {}"
            ]
            with open('dictionary_data.txt', 'w') as f:
                for line in sample_data:
                    f.write(line + '\n')

        ########## PYTHON SYNTAX & CODE SNIPPETS ##########
        python_syntax = {
            "1": {"type": "keyword", "keyword": "def", "position_pattern": "beginning", "csid": "1"},
            "2": {"type": "keyword", "keyword": "class", "position_pattern": "beginning", "csid": "2"},
            "3": {"type": "keyword", "keyword": "if", "position_pattern": "middle", "csid": "3"}
        }
        
        if not os.path.exists('python_syntax.json'):
            with open('python_syntax.json', 'w') as f:
                json.dump(python_syntax, f, indent=2)

        code_snippets = {
            "1": {"csid": "1", "function": "function_definition", "position_pattern": "beginning", 
                  "code_snippet": "def function_name(parameters):\\n    # Function body\\n    return result",
                  "synonymous_topics": ["function", "method", "definition"], "syntax": "def"},
            "2": {"csid": "2", "function": "class_definition", "position_pattern": "beginning",
                  "code_snippet": "class ClassName:\\n    def __init__(self, parameters):\\n        self.attribute = parameters",
                  "synonymous_topics": ["class", "object", "blueprint"], "syntax": "class"}
        }
        
        if not os.path.exists('code_snippets.json'):
            with open('code_snippets.json', 'w') as f:
                json.dump(code_snippets, f, indent=2)

    ###############################################################################
    # CONFIGURATION LOADING
    ###############################################################################

    def load_config_files(self):
        """Load all configuration files"""
        ########## WORD LISTS ##########
        self.question_words = self._load_word_list('question_words.txt')
        self.answer_words = self._load_word_list('answer_words.txt')
        self.fact_words = self._load_word_list('fact_words.txt')
        self.theory_words = self._load_word_list('theory_words.txt')
        self.past_indicators = self._load_word_list('past_indicators.txt')
        self.future_indicators = self._load_word_list('future_indicators.txt')
        
        ########## PLURAL RULES ##########
        self._load_plural_rules()
        
        ########## GRAMMAR RULES ##########
        self._load_grammar_rules()
        
        ########## EXPERT FIELDS ##########
        self._load_expert_fields()

    def _load_word_list(self, filename):
        """Load a word list from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return [line.strip().lower() for line in f if line.strip()]
        return []

    def _load_plural_rules(self):
        """Load plural rules from file"""
        if os.path.exists('plural_rules.json'):
            with open('plural_rules.json', 'r') as f:
                self.plural_rules = json.load(f)
        else:
            self.plural_rules = {}

    def _load_grammar_rules(self):
        """Load grammar rules based on mode"""
        with open('grammar_flow_formal.json', 'r') as f:
            formal_rules = json.load(f)
        
        if self.mode == 'formal':
            self.grammar_rules = formal_rules
        else:
            with open('grammar_flow_casual.json', 'r') as f:
                casual_rules = json.load(f)
            self.grammar_rules = formal_rules.copy()
            for key in casual_rules:
                if key in self.grammar_rules:
                    self.grammar_rules[key].update(casual_rules[key])
                else:
                    self.grammar_rules[key] = casual_rules[key]

    def _load_expert_fields(self):
        """Load expert fields configuration"""
        if os.path.exists('expert_fields.json'):
            with open('expert_fields.json', 'r') as f:
                self.expert_fields = json.load(f)
        else:
            self.expert_fields = {}

    ###############################################################################
    # DICTIONARY MANAGEMENT
    ###############################################################################

    def import_dictionary(self, file_path='dictionary_data.txt'):
        """Import dictionary data"""
        if not os.path.exists(file_path):
            print(f"Dictionary file {file_path} not found.")
            return
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if not line.strip() or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(';')]
                    if len(parts) < 2:
                        continue
                    
                    word_class, word = parts[0], parts[1].lower()
                    if word in self.word_db:
                        continue
                    
                    self.word_db[word] = {
                        'class': word_class, 'singular': parts[2] if len(parts) > 2 else word,
                        'plural': parts[3] if len(parts) > 3 else '',
                        'synonyms': [s.strip().lower() for s in parts[4].split(',')] if len(parts) > 4 and parts[4] else [],
                        'antonyms': [a.strip().lower() for a in parts[5].split(',')] if len(parts) > 5 and parts[5] else [],
                        'meaning': parts[6] if len(parts) > 6 else '',
                        'acronyms': [ac.strip().lower() for ac in parts[7].split(',')] if len(parts) > 7 and parts[7] else [],
                        'pattern_data': json.loads(parts[8]) if len(parts) > 8 and parts[8] else {},
                        'expert_field': 'general'  # Default expert field
                    }
                    
                    self._build_relationships(word)
                    self._check_partial_matches(word)
            
            print(f"Imported {len(self.word_db)} words from dictionary")
            self._add_punctuation_and_numbers()
            
            ########## TRAINING PROCESSES ##########
            if self.operation_mode == 'training':
                self._bridge_synonyms()
                self._bridge_antonyms()
                self._bridge_experts()
                self._infer_unknown_word_classes()
            
        except Exception as e:
            print(f"Error importing dictionary: {e}")

    def _add_punctuation_and_numbers(self):
        """Add punctuation and numbers to dictionary"""
        for char in '!,.?;:~"\'()[]{}':
            if char not in self.word_db:
                self.word_db[char] = {
                    'class': 'punctuation', 'singular': char, 'plural': '',
                    'synonyms': [], 'antonyms': [], 'meaning': f'punctuation: {char}',
                    'acronyms': [], 'pattern_data': {}, 'expert_field': 'general'
                }
        
        for i in range(10):
            num_str = str(i)
            if num_str not in self.word_db:
                self.word_db[num_str] = {
                    'class': 'number', 'singular': num_str, 'plural': '',
                    'synonyms': [], 'antonyms': [], 'meaning': f'number: {num_str}',
                    'acronyms': [], 'pattern_data': {}, 'expert_field': 'general'
                }

    ###############################################################################
    # ENHANCEMENTS INITIALIZATION
    ###############################################################################

    def _initialize_enhancements(self):
        """Initialize all enhancement systems"""
        ########## CONTEXT MEMORY ##########
        self.conversation_history = []
        self.context_window = 10
        self.current_context = {}
        
        ########## EMOTIONAL TONE ##########
        self.emotional_tones = {
            'formal': {'weight': 1.0, 'words': ['therefore', 'however', 'thus']},
            'casual': {'weight': 0.8, 'words': ['hey', 'cool', 'awesome']},
            'technical': {'weight': 1.2, 'words': ['algorithm', 'parameter', 'execute']},
            'empathetic': {'weight': 1.1, 'words': ['understand', 'feel', 'support']}
        }
        self.current_tone = 'neutral'
        
        ########## LEARNING SYSTEM ##########
        self.learning_rate = 0.1
        self.feedback_history = []
        
        ########## DOMAIN SPECIALIZATION ##########
        self.specialists = {'general': {'vocabulary': set(), 'patterns': defaultdict(lambda: defaultdict(float)), 'weight': 1.0}}
        self.current_domain = 'general'
        
        ########## CREATIVITY SETTINGS ##########
        self.creativity_level = 0.5
        self.creativity_boost = 0.3
        
        ########## PERFORMANCE OPTIMIZATION ##########
        self.prediction_cache = {}
        self.cache_size_limit = 1000
        
        ########## USER PROFILES ##########
        self.user_profiles = defaultdict(lambda: {
            'preferred_words': set(), 'common_topics': defaultdict(int),
            'writing_style': 'neutral', 'learning_adaptation': 1.0, 'interaction_count': 0
        })
        self.current_user = 'default'

    ###############################################################################
    # BRIDGING SYSTEMS
    ###############################################################################

    def _bridge_synonyms(self):
        """Bridge synonyms across the entire dictionary"""
        print("Bridging synonyms across dictionary...")
        bridges_created = 0
        
        for word, data in self.word_db.items():
            all_synonyms = set(data['synonyms'])
            for synonym in data['synonyms'][:]:
                if synonym in self.word_db:
                    synonym_data = self.word_db[synonym]
                    for sub_synonym in synonym_data['synonyms']:
                        if sub_synonym != word and sub_synonym not in all_synonyms:
                            all_synonyms.add(sub_synonym)
                            bridges_created += 1
            
            if all_synonyms != set(data['synonyms']):
                data['synonyms'] = list(all_synonyms)
                for new_synonym in all_synonyms:
                    if new_synonym not in self.word_relationships[word]:
                        self.word_relationships[word][new_synonym] += 2.0
                        self.word_relationships[new_synonym][word] += 2.0
        
        print(f"Created {bridges_created} synonym bridges")

    def _bridge_antonyms(self):
        """Bridge antonyms across the entire dictionary"""
        print("Bridging antonyms across dictionary...")
        bridges_created = 0
        
        for word, data in self.word_db.items():
            all_antonyms = set(data['antonyms'])
            for antonym in data['antonyms'][:]:
                if antonym in self.word_db:
                    antonym_data = self.word_db[antonym]
                    for sub_antonym in antonym_data['antonyms']:
                        if sub_antonym != word and sub_antonym not in all_antonyms:
                            all_antonyms.add(sub_antonym)
                            bridges_created += 1
            
            if all_antonyms != set(data['antonyms']):
                data['antonyms'] = list(all_antonyms)
                for new_antonym in all_antonyms:
                    if new_antonym not in self.word_relationships[word]:
                        self.word_relationships[word][new_antonym] -= 1.5
                        self.word_relationships[new_antonym][word] -= 1.5
        
        print(f"Created {bridges_created} antonym bridges")

    def _bridge_experts(self):
        """Bridge words to expert fields based on meaning and usage"""
        print("Bridging expert fields...")
        expert_links_created = 0
        
        for word, data in self.word_db.items():
            best_expert = self._deduce_expert_field(word, data)
            if best_expert != 'general' and data['expert_field'] == 'general':
                data['expert_field'] = best_expert
                expert_links_created += 1
        
        print(f"Created {expert_links_created} expert field links")

    def _deduce_expert_field(self, word, data):
        """Deduce the most likely expert field for a word"""
        expert_scores = defaultdict(float)
        meaning = data['meaning'].lower()
        
        for expert, expert_data in self.expert_fields.items():
            # Score based on meaning keywords
            for keyword in expert_data['keywords']:
                if keyword in meaning:
                    expert_scores[expert] += expert_data['weight']
            
            # Score based on synonyms in expert field
            for synonym in data['synonyms']:
                if synonym in self.word_db and self.word_db[synonym]['expert_field'] == expert:
                    expert_scores[expert] += 0.5
        
        if expert_scores:
            return max(expert_scores.items(), key=lambda x: x[1])[0]
        return 'general'

    ###############################################################################
    # CONTEXT DEDUCTION SYSTEM
    ###############################################################################

    def _deduce_context(self, text):
        """Deduce the highest probability topic and expert field"""
        words = [w for w in re.findall(r'\b\w+\b', text.lower()) if w not in string.punctuation]
        
        ########## NOUN ANALYSIS ##########
        nouns = [word for word in words if self._get_word_class(word) == 'noun']
        noun_weights = {}
        
        if nouns:
            # Weight first noun highest
            if nouns:
                noun_weights[nouns[0]] = 2.0
            
            # Weight repeated nouns
            noun_counts = Counter(nouns)
            for noun, count in noun_counts.items():
                noun_weights[noun] = noun_weights.get(noun, 0) + (count * 0.5)
            
            # Include synonyms of nouns
            for noun in nouns:
                for synonym in self.word_db.get(noun, {}).get('synonyms', []):
                    noun_weights[synonym] = noun_weights.get(synonym, 0) + 0.3
        
        ########## EXPERT FIELD DEDUCTION ##########
        expert_scores = defaultdict(float)
        for word in words:
            if word in self.word_db:
                expert_field = self.word_db[word]['expert_field']
                if expert_field != 'general':
                    expert_scores[expert_field] += 1.0
        
        ########## TOPIC SELECTION ##########
        if noun_weights:
            main_topic = max(noun_weights.items(), key=lambda x: x[1])[0]
        else:
            main_topic = words[0] if words else "general"
        
        main_expert = max(expert_scores.items(), key=lambda x: x[1])[0] if expert_scores else 'general'
        
        return {
            'main_topic': main_topic,
            'main_expert': main_expert,
            'topic_confidence': max(noun_weights.values()) if noun_weights else 0.0,
            'expert_confidence': max(expert_scores.values()) if expert_scores else 0.0
        }

    ###############################################################################
    # RELATIONSHIP BUILDING
    ###############################################################################

    def _build_relationships(self, word):
        """Build word relationships"""
        data = self.word_db[word]
        
        # Synonym relationships
        for synonym in data['synonyms']:
            self.word_relationships[word][synonym] += 2.0
            self.word_relationships[synonym][word] += 2.0
        
        # Antonym relationships
        for antonym in data['antonyms']:
            self.word_relationships[word][antonym] -= 1.5
            self.word_relationships[antonym][word] -= 1.5
        
        # Acronym relationships
        for acronym in data['acronyms']:
            self.word_relationships[word][acronym] += 1.0
            self.word_relationships[acronym][word] += 1.0
        
        # Class-based relationships
        word_class = data['class']
        common_pairs = self.grammar_rules.get('common_pairs', {})
        if word_class in common_pairs:
            for other_word, other_data in self.word_db.items():
                if other_word != word and other_data['class'] in common_pairs[word_class]:
                    self.word_relationships[word][other_word] += 0.3

    def _check_partial_matches(self, word):
        """Check for partial word matches"""
        for i in range(1, len(word)):
            partial = word[:i]
            if partial in self.word_db:
                weight = 0.5 * (i / len(word))
                self.word_relationships[word][partial] += weight
                self.word_relationships[partial][word] += weight

    ###############################################################################
    # PATTERN ANALYSIS
    ###############################################################################

    def analyze_patterns(self, sentence):
        """Analyze sentence patterns and relationships"""
        words = re.findall(r'\b\w+\b|[^\w\s]', sentence.lower())
        result = {
            'word_classes': [],
            'sentence_type': self._detect_sentence_type(words),
            'tense': self._detect_tense(words),
            'relationship_patterns': [],
            'known_words_ratio': self._calculate_known_words_ratio(words),
            'position_patterns': [],
            'context': self._deduce_context(sentence)
        }
        
        for i, word in enumerate(words):
            if word in string.punctuation:
                continue
                
            word_class = self._get_word_class(word)
            result['word_classes'].append((word, word_class))
            
            self._build_relationship_patterns(word, words, i)
            
            position_type = self._get_word_position(i, len(words))
            result['position_patterns'].append(f"{word} ({position_type})")
            
            if self.operation_mode == 'training':
                self._update_word_position_data(word, position_type)
            
            if i > 0 and words[i-1] not in string.punctuation:
                prev_word = words[i-1]
                relationship_strength = self._calculate_pattern_relationship(prev_word, word, words, i)
                result['relationship_patterns'].append(f"{prev_word} -> {word}: {relationship_strength:.3f}")
        
        return result

    def _build_relationship_patterns(self, current_word, all_words, current_index):
        """Build pattern relationships between words"""
        for i, other_word in enumerate(all_words):
            if i == current_index or other_word in string.punctuation:
                continue
                
            relationship_strength = self._calculate_pattern_relationship(current_word, other_word, all_words, current_index)
            
            if i < current_index:
                self.pattern_relationships[current_word]['before'][other_word] += relationship_strength
            else:
                self.pattern_relationships[current_word]['after'][other_word] += relationship_strength
            
            sentence_position = self._get_word_position(i, len(all_words))
            if 'position_context' not in self.pattern_relationships[current_word]:
                self.pattern_relationships[current_word]['position_context'] = defaultdict(lambda: defaultdict(float))
            
            self.pattern_relationships[current_word]['position_context'][sentence_position][other_word] += relationship_strength

    ###############################################################################
    # PREDICTION SYSTEM
    ###############################################################################

    def predict_next(self, text, mode='simple'):
        """Predict next word(s)"""
        words = [w for w in re.findall(r'\b\w+\b', text.lower()) if w not in string.punctuation]
        if not words:
            return []
        
        known_ratio = self._calculate_known_words_ratio(re.findall(r'\b\w+\b|[^\w\s]', text.lower()))
        
        if mode == 'simple':
            predictions = self._simple_relationship_prediction(words)
        else:
            predictions = self._complex_relationship_prediction(words)
        
        return predictions, known_ratio

    def _simple_relationship_prediction(self, words):
        """Simple prediction mode"""
        last_word = words[-1]
        scores = defaultdict(float)
        
        for related_word, rel_strength in self.word_relationships[last_word].items():
            if rel_strength > 0:
                scores[related_word] += rel_strength * 0.5
        
        for next_word, pattern_strength in self.pattern_relationships[last_word]['after'].items():
            scores[next_word] += pattern_strength * 0.3
        
        last_class = self._get_word_class(last_word)
        expected_classes = self._get_expected_classes(last_class)
        for word, data in self.word_db.items():
            if data['class'] in expected_classes:
                scores[word] += 0.2
        
        return self._get_top_predictions(scores)

    def _complex_relationship_prediction(self, words):
        """Complex prediction mode"""
        last_word = words[-1]
        scores = defaultdict(float)
        
        for candidate_word in self.word_db:
            if candidate_word == last_word:
                continue
                
            total_score = 0.0
            direct_rel = self.word_relationships[last_word][candidate_word]
            total_score += max(0, direct_rel) * 0.3
            
            pattern_rel = self.pattern_relationships[last_word]['after'][candidate_word]
            total_score += pattern_rel * 0.25
            
            grammatical_score = self._calculate_grammatical_flow(last_word, candidate_word)
            total_score += grammatical_score * 0.20
            
            contextual_score = self._calculate_contextual_coherence(candidate_word, words)
            total_score += contextual_score * 0.15
            
            field_score = self._calculate_field_consistency(candidate_word, words)
            total_score += field_score * 0.10
            
            if total_score > 0:
                scores[candidate_word] = total_score
        
        return self._get_top_predictions(scores)

    ###############################################################################
    # ENHANCED FEATURES
    ###############################################################################

    def enhanced_predict_next(self, text, mode='complex'):
        """Enhanced prediction without flag processing (flags handled in main)"""
        # Reset flags at the start (safety measure)
        self.internet_enabled = False
        self.code_enabled = False
        self.image_enabled = False
        self.ascii_enabled = False
        
        # If no text after flag processing, return empty
        if not text.strip():
            return [], 100
        
        # Get base predictions
        base_predictions, known_ratio = self.predict_next(text, mode)
        
        if not base_predictions:
            return base_predictions, known_ratio
        
        # Apply all enhancement layers
        enhanced_predictions = base_predictions
        
        # Context awareness
        enhanced_predictions = self.get_contextual_predictions(text, enhanced_predictions)
        
        # Emotional tone adaptation
        tone = self.detect_emotional_tone(text)
        enhanced_predictions = self.adapt_to_tone(enhanced_predictions)
        
        # Domain specialization
        domain = self.detect_domain(text)
        enhanced_predictions = self.get_domain_enhanced_predictions(text, enhanced_predictions)
        
        # Creativity enhancement
        enhanced_predictions = self.get_creative_predictions(text.split(), enhanced_predictions)
        
        # Personalization
        enhanced_predictions = self.get_personalized_predictions(enhanced_predictions)
        
        return enhanced_predictions, known_ratio
    ###############################################################################
    # SPECIALIZED MODULES
    ###############################################################################

    def internet_search(self, query):
        """Internet search functionality"""
        if not self.internet_enabled:
            return "Internet search disabled. Use --internet flag to enable."
        
        # Placeholder for internet search implementation
        return f"Internet search for: {query} - [Implementation needed]"

    def python_code_generation(self, context):
        """Python code generation based on context"""
        if not self.code_enabled:
            return "Code generation disabled. Use --code flag to enable."
        
        # Placeholder for code generation
        return f"Python code for: {context} - [Implementation needed]"

    def image_processing(self, description):
        """Image processing and generation"""
        if not self.image_enabled:
            return "Image processing disabled. Use --image flag to enable."
        
        # Placeholder for image processing
        return f"Image processing for: {description} - [Implementation needed]"

    ###############################################################################
    # UTILITY FUNCTIONS
    ###############################################################################

    def _get_word_class(self, word):
        """Get word class with partial matching"""
        if word in self.word_db:
            return self.word_db[word]['class']
        
        for i in range(1, len(word) + 1):
            partial = word[:i]
            if partial in self.word_db:
                return self.word_db[partial]['class']
        
        return 'unknown'

    def _get_word_position(self, index, total_words):
        """Determine word position in sentence"""
        if total_words <= 1:
            return 'single_word'
        elif index == 0:
            return 'beginning_sentence'
        elif index == total_words - 1:
            return 'end_sentence'
        else:
            return 'middle_sentence'

    def _calculate_known_words_ratio(self, words):
        """Calculate percentage of known words"""
        word_count = len([w for w in words if w not in string.punctuation])
        if word_count == 0:
            return 0
        known_count = len([w for w in words if w not in string.punctuation and self._get_word_class(w) != 'unknown'])
        return (known_count / word_count) * 100

    def _detect_sentence_type(self, words):
        """Detect sentence type"""
        if any(w in self.question_words for w in words):
            return 'question'
        elif any(w in self.answer_words for w in words):
            return 'answer'
        elif any(w in self.fact_words for w in words):
            return 'fact'
        elif any(w in self.theory_words for w in words):
            return 'theory'
        return 'statement'

    def _detect_tense(self, words):
        """Detect tense"""
        if any(any(indicator in w for indicator in self.past_indicators) for w in words):
            return 'past'
        if any(any(indicator in w for indicator in self.future_indicators) for w in words):
            return 'future'
        return 'present'

    def _calculate_pattern_relationship(self, word1, word2, all_words, current_index):
        """Calculate relationship strength"""
        strength = 0.0
        direct_rel = self.word_relationships[word1][word2]
        strength += abs(direct_rel) * 0.4
        
        semantic_weight = self._calculate_semantic_proximity(word1, word2, all_words, current_index)
        strength += semantic_weight * 0.25
        
        grammatical_weight = self._calculate_grammatical_compatibility(word1, word2)
        strength += grammatical_weight * 0.20
        
        contextual_weight = self._calculate_contextual_relevance(word1, word2, all_words)
        strength += contextual_weight * 0.15
        
        return max(0.0, strength)

    def _calculate_grammatical_compatibility(self, word1, word2):
        """Calculate grammatical compatibility"""
        class1 = self._get_word_class(word1)
        class2 = self._get_word_class(word2)
        compatibility_rules = self.grammar_rules.get('compatibility_rules', {})
        return compatibility_rules.get(class1, {}).get(class2, 0.1)

    def _calculate_semantic_proximity(self, word1, word2, all_words, current_index):
        """Calculate semantic proximity"""
        proximity = 0.0
        shared_connections = sum(1 for word in self.word_relationships[word1] 
                               if word in self.word_relationships[word2] and self.word_relationships[word2][word] > 0)
        proximity += shared_connections * 0.2
        
        word2_index = all_words.index(word2) if word2 in all_words else current_index
        distance = abs(current_index - word2_index)
        if distance > 0:
            proximity += (1.0 / distance) * 0.3
        
        return min(1.0, proximity)

    def _calculate_contextual_relevance(self, word1, word2, all_words):
        """Calculate contextual relevance"""
        relevance = 0.0
        theme_words = [w for w in all_words if w not in [word1, word2] and w not in string.punctuation]
        
        shared_theme_connections = sum(1 for theme_word in theme_words[:3]
                                     if (self.word_relationships[word1][theme_word] > 0 and 
                                         self.word_relationships[word2][theme_word] > 0))
        relevance += shared_theme_connections * 0.2
        
        return min(0.5, relevance)

    def _calculate_grammatical_flow(self, last_word, candidate_word):
        """Calculate grammatical flow"""
        last_class = self._get_word_class(last_word)
        candidate_class = self._get_word_class(candidate_word)
        flow_rules = self.grammar_rules.get('flow_rules', {})
        return flow_rules.get(last_class, {}).get(candidate_class, 0.1)

    def _calculate_contextual_coherence(self, candidate_word, previous_words):
        """Calculate contextual coherence"""
        coherence = 0.0
        for prev_word in previous_words[-3:]:
            if prev_word in self.word_relationships[candidate_word]:
                rel_strength = self.word_relationships[candidate_word][prev_word]
                if rel_strength > 0:
                    coherence += rel_strength * 0.2
        return min(1.0, coherence)

    def _calculate_field_consistency(self, candidate_word, previous_words):
        """Calculate field consistency"""
        candidate_field = self._get_semantic_field(candidate_word)
        if candidate_field == 'general':
            return 0.3
        
        field_matches = sum(1 for prev_word in previous_words[-2:] 
                          if self._get_semantic_field(prev_word) == candidate_field)
        return field_matches * 0.2

    def _get_semantic_field(self, word):
        """Get semantic field"""
        if word in self.word_db:
            meaning = self.word_db[word]['meaning'].lower()
            if any(term in meaning for term in ['computer', 'digital', 'electronic']):
                return 'technology'
            elif any(term in meaning for term in ['science', 'research', 'study']):
                return 'science'
            elif any(term in meaning for term in ['math', 'calculate', 'number']):
                return 'mathematics'
        return 'general'

    def _get_expected_classes(self, current_class):
        """Get expected next word classes"""
        flow_rules = self.grammar_rules.get('flow_rules', {})
        expected = list(flow_rules.get(current_class, {}).keys())
        return expected if expected else ['noun', 'verb']

    def _get_top_predictions(self, scores, top_n=10):
        """Get top predictions"""
        return sorted([(word, score) for word, score in scores.items() if score > 0],
                     key=lambda x: x[1], reverse=True)[:top_n]

    def _update_word_position_data(self, word, position_type):
        """Update word position data"""
        if word in self.word_db:
            if 'position_patterns' not in self.word_db[word]['pattern_data']:
                self.word_db[word]['pattern_data']['position_patterns'] = {}
            
            self.word_db[word]['pattern_data']['position_patterns'][position_type] = \
                self.word_db[word]['pattern_data']['position_patterns'].get(position_type, 0) + 1

    def _infer_unknown_word_classes(self):
        """Infer word classes for unknown words"""
        print("Inferring word classes for unknown words...")
        inferred_count = 0
        
        for word, data in self.word_db.items():
            if data['class'] == 'unknown':
                inferred_class = self._infer_word_class_from_patterns(word)
                if inferred_class != 'unknown':
                    data['class'] = inferred_class
                    inferred_count += 1
        
        print(f"Inferred word classes for {inferred_count} words")

    def _infer_word_class_from_patterns(self, word):
        """Infer word class from patterns"""
        class_scores = defaultdict(float)
        compatibility_rules = self.grammar_rules.get('compatibility_rules', {})
        
        for position in ['before', 'after']:
            for context_word, strength in self.pattern_relationships[word][position].items():
                if context_word in self.word_db:
                    context_class = self.word_db[context_word]['class']
                    for test_class in ['noun', 'verb', 'adjective', 'adverb']:
                        if test_class in compatibility_rules.get(context_class, {}):
                            class_scores[test_class] += strength * compatibility_rules[context_class][test_class]
        
        for other_word, other_data in self.word_db.items():
            if word in other_data['synonyms'] and other_data['class'] != 'unknown':
                class_scores[other_data['class']] += 1.0
        
        if class_scores:
            return max(class_scores.items(), key=lambda x: x[1])[0]
        
        return 'unknown'

    ###############################################################################
    # ENHANCEMENT METHODS (From previous implementation)
    ###############################################################################

    def update_conversation_history(self, user_input, ai_response):
        """Update conversation history"""
        self.conversation_history.append(("user", user_input))
        self.conversation_history.append(("ai", ai_response))
        if len(self.conversation_history) > self.context_window * 2:
            self.conversation_history = self.conversation_history[-self.context_window * 2:]

    def detect_emotional_tone(self, text):
        """Detect emotional tone"""
        tone_scores = defaultdict(float)
        words = text.lower().split()
        for tone, data in self.emotional_tones.items():
            for tone_word in data['words']:
                if tone_word in words:
                    tone_scores[tone] += data['weight']
        self.current_tone = max(tone_scores.items(), key=lambda x: x[1])[0] if tone_scores else 'neutral'
        return self.current_tone

    def adapt_to_tone(self, predictions):
        """Adapt to emotional tone"""
        if self.current_tone == 'neutral':
            return predictions
        tone_data = self.emotional_tones.get(self.current_tone, {'weight': 1.0, 'words': []})
        tone_adjusted = []
        for word, score in predictions:
            if word in tone_data['words']:
                adjusted_score = score * tone_data['weight']
            else:
                adjusted_score = score
            tone_adjusted.append((word, adjusted_score))
        return sorted(tone_adjusted, key=lambda x: x[1], reverse=True)

    def get_contextual_predictions(self, text, base_predictions):
        """Get contextual predictions"""
        context = self._deduce_context(text)
        if not context['main_topic']:
            return base_predictions
        contextual_predictions = []
        for word, score in base_predictions:
            context_boost = 0.0
            if context['main_topic'] in self.word_relationships and word in self.word_relationships[context['main_topic']]:
                context_boost = self.word_relationships[context['main_topic']][word] * 0.1
            contextual_score = score * (1 + context_boost)
            contextual_predictions.append((word, contextual_score))
        return sorted(contextual_predictions, key=lambda x: x[1], reverse=True)

    def detect_domain(self, text):
        """Detect domain"""
        domain_scores = defaultdict(float)
        words = set(text.lower().split())
        for domain, data in self.specialists.items():
            overlap = words.intersection(data['vocabulary'])
            domain_scores[domain] = len(overlap) * data['weight']
        self.current_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
        return self.current_domain

    def get_domain_enhanced_predictions(self, text, base_predictions):
        """Get domain-enhanced predictions"""
        if self.current_domain == 'general':
            return base_predictions
        domain_data = self.specialists[self.current_domain]
        domain_enhanced = []
        for word, score in base_predictions:
            if word in domain_data['vocabulary']:
                enhanced_score = score * domain_data['weight']
            else:
                enhanced_score = score
            domain_enhanced.append((word, enhanced_score))
        return sorted(domain_enhanced, key=lambda x: x[1], reverse=True)

    def get_creative_predictions(self, words, base_predictions):
        """Get creative predictions"""
        if self.creativity_level < 0.1:
            return base_predictions
        creative_predictions = []
        for word, score in base_predictions:
            if score < 0.7:
                creative_score = score * (1 + self.creativity_boost)
            else:
                creative_score = score
            creative_predictions.append((word, creative_score))
        return sorted(creative_predictions, key=lambda x: x[1], reverse=True)

    def get_personalized_predictions(self, base_predictions):
        """Get personalized predictions"""
        profile = self.user_profiles.get(self.current_user, self.user_profiles['default'])
        if not profile['preferred_words']:
            return base_predictions
        personalized = []
        for word, score in base_predictions:
            if word in profile['preferred_words']:
                personalized_score = score * (1 + profile['learning_adaptation'] * 0.2)
            else:
                personalized_score = score
            personalized.append((word, personalized_score))
        return sorted(personalized, key=lambda x: x[1], reverse=True)

    def set_mode(self, mode, operation_mode='speech'):
        """Set mode and operation mode"""
        self.mode = mode
        self.operation_mode = operation_mode
        self.load_config_files()
    
    # Add this method to the ExpertFieldLLM class in your main file:

    def generate_sentence(self, text, predictions):
        """Generate grammatical sentence using word class patterns with word limits"""
        input_words = [w for w in re.findall(r'\b\w+\b', text.lower()) if w not in string.punctuation]
        if not input_words:
            return text
            
        sentence_type = self._detect_sentence_type(input_words)
        
        # Get most probable word classes based on current context
        expected_classes = self._get_most_probable_classes(input_words, predictions)
        
        generated_words = input_words.copy()
        
        # Generate continuation based on expected word classes, respecting max words
        for expected_class in expected_classes:
            if len(generated_words) >= self.max_words:
                break
                
            # Find best word for this class from predictions
            best_word = self._find_best_word_for_class(predictions, expected_class, generated_words)
            if best_word:
                generated_words.append(best_word)
        
        # Ensure minimum word count if we have predictions available
        while len(generated_words) < self.min_words and predictions:
            # Get the next best word that's not already used
            for word, score in predictions:
                if (word not in generated_words and 
                    self._is_grammatically_compatible(generated_words[-1] if generated_words else '', word)):
                    generated_words.append(word)
                    break
            else:
                # No suitable words found, break to avoid infinite loop
                break
        
        # Final check to respect max words (in case min was too aggressive)
        if len(generated_words) > self.max_words:
            generated_words = generated_words[:self.max_words]
        
        # Capitalize first word and add punctuation
        if generated_words:
            generated_words[0] = generated_words[0].capitalize()
            sentence = ' '.join(generated_words)
            
            if sentence_type == 'question':
                sentence += '?'
            else:
                # Only add period if it's a complete sentence
                if len(generated_words) >= 3:  # At least subject + verb + object
                    sentence += '.'
            
            return sentence
    
        return text
    
    def _get_most_probable_classes(self, input_words, predictions):
        """Get most probable word classes based on context and predictions"""
        class_weights = defaultdict(float)
        
        # Weight by grammar rules
        sentence_type = self._detect_sentence_type(input_words)
        sentence_order = self.grammar_rules.get('sentence_order', {}).get(sentence_type, ['noun', 'verb', 'noun'])
        
        for i, expected_class in enumerate(sentence_order[len(input_words):]):
            class_weights[expected_class] += 1.0 / (i + 1)  # Higher weight for earlier positions
        
        # Weight by prediction word classes
        for word, score in predictions:
            word_class = self._get_word_class(word)
            class_weights[word_class] += score * 0.5
        
        # Return classes sorted by weight
        return [cls for cls, weight in sorted(class_weights.items(), key=lambda x: x[1], reverse=True)]
    
    def _find_best_word_for_class(self, predictions, target_class, existing_words):
        """Find the best word from predictions for a specific word class"""
        candidates = []
        
        for word, score in predictions:
            if (self._get_word_class(word) == target_class and 
                word not in existing_words and
                self._is_grammatically_compatible(existing_words[-1] if existing_words else '', word)):
                # Apply additional scoring based on pattern relationships
                pattern_score = 0.0
                if existing_words:
                    last_word = existing_words[-1]
                    pattern_score = self.pattern_relationships[last_word]['after'].get(word, 0.0) * 0.3
                
                total_score = score + pattern_score
                candidates.append((word, total_score))
        
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        return None
    
    def _is_grammatically_compatible(self, last_word, candidate_word):
        """Check if candidate word is grammatically compatible with last word"""
        if not last_word:
            return True
            
        last_class = self._get_word_class(last_word)
        candidate_class = self._get_word_class(candidate_word)
        flow_rules = self.grammar_rules.get('flow_rules', {})
        
        return flow_rules.get(last_class, {}).get(candidate_class, 0) > 0.3

###############################################################################
# MAIN APPLICATION
###############################################################################

def main():
    llm = ExpertFieldLLM()
    
    print("\n=== Expert Field LLM ===")
    print("Select operation mode:")
    print("1. File training mode")
    print("2. Speech training mode") 
    print("3. Speech mode")
    
    operation_choice = input("Enter choice (1, 2, or 3): ").strip()
    if operation_choice == '1':
        operation_mode = 'file_training'
    elif operation_choice == '2':
        operation_mode = 'speech_training'
    else:
        operation_mode = 'speech'
    
    print("\nSelect formality mode:")
    print("1. Formal mode")
    print("2. Casual mode")
    
    mode_choice = input("Enter choice (1 or 2): ").strip()
    if mode_choice == '1':
        mode = 'formal'
    else:
        mode = 'casual'
    
    llm.set_mode(mode, operation_mode)
    print(f"\nStarting in {mode} {operation_mode} mode...")
    
    if operation_mode == 'speech':
        print("\n🚀 Speech Mode Active")
        print("💡 Special Commands:")
        print("   --internet [query]  - Search the web")
        print("   --code [description] - Generate Python code") 
        print("   --image            - Analyze images (place 'input_image.png' in folder)")
        print("   --asciiimage       - Create ASCII art from image")
        print("   --min[number]      - Set minimum words in response")
        print("   --max[number]      - Set maximum words in response")
        print("   /gobackprogram0    - Return to menu")
        print("   /quitprogram0      - Exit completely\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input == '/quitprogram0':
                print("👋 Goodbye!")
                break
            elif user_input == '/gobackprogram0':
                print("🔄 Returning to menu...")
                main()
                return
            
            if not user_input:
                continue
            
            # Handle special commands FIRST
            # Handle word count settings FIRST (before any other processing)
            min_match = re.search(r'--min(\d+)', user_input)
            max_match = re.search(r'--max(\d+)', user_input)
            
            if min_match or max_match:
                # Extract and set the values
                if min_match:
                    llm.min_words = int(min_match.group(1))
                    user_input = user_input.replace(min_match.group(0), '').strip()
                    print(f"Minimum words set to: {llm.min_words}")
                
                if max_match:
                    llm.max_words = int(max_match.group(1))
                    user_input = user_input.replace(max_match.group(0), '').strip()
                    print(f"Maximum words set to: {llm.max_words}")
                
                # If only flags were provided, show confirmation and continue
                if not user_input.strip():
                    print("Word limits updated. Please enter your message.")
                    continue
            
            # Handle special commands
            if '--internet' in user_input:
                print("Internet search activated...")
                llm.internet_enabled = True
                result = llm.internet_search(user_input)
                print(f"\nAssistant: {result}")
                continue
                
            elif '--code' in user_input:
                print("Code generation activated...")
                llm.code_enabled = True
                result = llm.python_code_generation(user_input)
                print(f"\nAssistant: {result}")
                continue
                
            elif '--image' in user_input or '--asciiimage' in user_input:
                print("Image processing activated...")
                llm.image_enabled = True
                if '--asciiimage' in user_input:
                    llm.ascii_enabled = True
                result = llm.image_processing(user_input)
                print(f"\nAssistant: {result}")
                continue
            
            # Normal text processing with enhanced predictions
            print("🤔 Processing your message...")
            predictions, known_ratio = llm.enhanced_predict_next(user_input, 'complex')
            
            if known_ratio < 50:
                print(f"❌ Assistant: Please rephrase the question ({known_ratio:.1f}% of words known)")
                continue
            
            if predictions:
                generated_sentence = llm.generate_sentence(user_input, predictions)
                
                # Apply word count limits
                words = generated_sentence.split()
                if len(words) > llm.max_words:
                    words = words[:llm.max_words]
                    generated_sentence = ' '.join(words) + '.'
                
                # Ensure minimum word count
                while len(words) < llm.min_words and len(predictions) > len(words):
                    if len(predictions) > len(words):
                        next_word = predictions[len(words)][0]
                        if next_word not in words:
                            words.append(next_word)
                            generated_sentence = ' '.join(words) + '.'
                    else:
                        break
                
                print(f"\n✅ Assistant: {generated_sentence}")
            else:
                print("❌ Assistant: I need more context to continue.")
            print()
    
    elif operation_mode == 'speech_training':
        print("\n🔬 Speech Training Mode Active")
        print("Type '/gobackprogram0' to return to menu")
        print("Type '/quitprogram0' to exit completely\n")
        
        while True:
            user_input = input("Enter sentence: ").strip()
            
            if user_input == '/quitprogram0':
                print("👋 Goodbye!")
                break
            elif user_input == '/gobackprogram0':
                print("🔄 Returning to menu...")
                main()
                return
            
            if not user_input:
                continue
            
            print("🔍 Analyzing patterns...")
            analysis = llm.analyze_patterns(user_input)
            predictions, known_ratio = llm.predict_next(user_input, 'complex')
            
            print(f"\n📊 Analysis for: '{user_input}'")
            print(f"📝 Sentence type: {analysis['sentence_type']}")
            print(f"⏰ Tense: {analysis['tense']}")
            print(f"📚 Known words: {analysis['known_words_ratio']:.1f}%")
            print(f"🎯 Context: {analysis['context']}")
            print(f"🔤 Word classes: {analysis['word_classes']}")
            print(f"📍 Position patterns: {analysis['position_patterns']}")
            
            if predictions:
                print("\n🎯 Top predictions:")
                for i, (word, score) in enumerate(predictions[:5], 1):
                    word_class = llm._get_word_class(word)
                    expert_field = llm.word_db.get(word, {}).get('expert_field', 'general')
                    print(f"  {i}. {word} ({word_class}, {expert_field}) - score: {score:.3f}")
            
            print("🔗 Top relationships:")
            for rel in analysis['relationship_patterns'][:3]:
                print(f"  {rel}")
            print()
    
    else:  # file_training mode
        print("\n📚 File Training Mode Active")
        
        total_words = len(llm.word_db)
        known_words = sum(1 for word in llm.word_db if llm.word_db[word]['class'] != 'unknown')
        
        print(f"📊 Total words in dictionary: {total_words}")
        print(f"✅ Known word classes: {known_words}")
        print(f"❓ Unknown word classes: {total_words - known_words}")
        
        # Show expert field distribution
        expert_counts = defaultdict(int)
        for word_data in llm.word_db.values():
            expert_counts[word_data.get('expert_field', 'general')] += 1
        
        print(f"\n🎯 Expert Field Distribution:")
        for expert, count in expert_counts.items():
            if expert != 'general':
                print(f"  {expert}: {count} words")
        
        print(f"\n✅ Training completed with:")
        print("  - Synonym bridges created")
        print("  - Antonym bridges created") 
        print("  - Expert field links established")
        print("  - Word classes inferred for unknown words")
        
        print(f"\n💡 Type '/gobackprogram0' to return to menu or '/quitprogram0' to exit")
        
        while True:
            command = input().strip()
            if command == '/quitprogram0':
                print("👋 Goodbye!")
                break
            elif command == '/gobackprogram0':
                print("🔄 Returning to menu...")
                main()
                return
main()