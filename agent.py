import os
import math
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from openai import OpenAI
# from transformers import AutoModelForCausalLM, AutoTokenizer
from constants import DEFAULT_MODEL

load_dotenv()

class BaseAgent(ABC):
    @abstractmethod
    def infer(self, prompt, sample=False):
        pass
    
    @abstractmethod
    def infer_score(self, prompts):
        pass
    
    @abstractmethod
    def batch_infer(self, prompts, batch_size=8, sample=False):
        pass

class APIAgent(BaseAgent):
    def __init__(self, model_name, _type: str):
        from constants import USE_SGLANG, SGLANG_CRAWLER_URL, SGLANG_SELECTOR_URL, OPENAI_BASE_URL
        
        if USE_SGLANG:
            # Use SGLang deployment
            if _type == "crawler":
                self.client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=SGLANG_CRAWLER_URL
                )
            else:  # selector
                self.client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=SGLANG_SELECTOR_URL
                )
        else:
            # Use DeepSeek API
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
            )
        
        self.model_name = model_name

    def infer_score(self, prompts):
        if len(prompts) == 0:
            return []
        
        token_probabilities = []
        for prompt in prompts:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=1,
                n=1,
                logprobs=True,
                top_logprobs=1,
            )

            logprobs_data = response.choices[0].logprobs.content[0].top_logprobs
            for item in logprobs_data:
                token_probabilities.append({
                    'token': item.token,
                    'logprob': item.logprob,
                    'probability': math.exp(item.logprob)
                })

        return token_probabilities
    
    def infer(self, prompt, sample=False):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.7 if sample else 0,
            max_tokens=512,
        )
        return response.choices[0].message.content
    
    def batch_infer(self, prompts, batch_size=8, sample=False):
        if len(prompts) == 0:
            return []
            
        responses = []
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i: i + batch_size]
            batch_responses = []
            
            for prompt in batch_prompts:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt.strip()}
                    ],
                    temperature=0.7 if sample else 0,
                    max_tokens=512
                )
                batch_responses.append(response.choices[0].message.content)
            responses.extend(batch_responses)
        return responses

# class LocalAgent(BaseAgent):
#     def __init__(self, model_path):
#         self.model = AutoModelForCausalLM.from_pretrained(
#             model_path,
#             torch_dtype="auto",
#             device_map="auto"
#         )
#         self.tokenizer = AutoTokenizer.from_pretrained(
#             model_path,
#             padding_side='left'
#         )
    
#     def infer_score(self, prompts):
#         if len(prompts) == 0:
#             return []
        
#         encoded_input = self.tokenizer(prompts, return_tensors='pt', padding=True, truncation=True)
#         input_ids = encoded_input.input_ids.to(self.model.device)
#         attention_mask = encoded_input.attention_mask.to(self.model.device)

#         outputs = self.model.generate(
#             input_ids=input_ids,
#             attention_mask=attention_mask,
#             max_new_tokens=1,
#             output_scores=True, 
#             return_dict_in_generate=True, 
#             do_sample=False
#         )
        
#         true_token_id = self.tokenizer.convert_tokens_to_ids('True')
#         probs = outputs.scores[0].softmax(dim=-1)[:, true_token_id].cpu().numpy().tolist()
        
#         result = []
#         for prob in probs:
#             result.append({
#                 'token': 'True',
#                 'logprob': math.log(prob) if prob > 0 else -100,
#                 'probability': prob
#             })
            
#         return result

#     def infer(self, prompt, sample=False):
#         text = self.tokenizer.apply_chat_template(
#             [{
#                 "content": prompt.strip(),
#                 "role":    "user"
#             }],
#             tokenize=False,
#             add_generation_prompt=True
#         )
#         model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
#         if sample:
#             model_inputs["do_sample"] = True
#             model_inputs["temperature"] = 2.0
#             model_inputs["top_p"] = 0.8

#         generated_ids = self.model.generate(
#             **model_inputs,
#             max_new_tokens=512
#         )
#         generated_ids = [
#             output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
#         ]

#         response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
#         return response
    
#     def batch_infer(self, prompts, batch_size=8, sample=False):
#         if len(prompts) == 0:
#             return []
            
#         texts = [self.tokenizer.apply_chat_template(
#             [{
#                 "content": prompt.strip(),
#                 "role":    "user"
#             }],
#             tokenize=False,
#             add_generation_prompt=True
#         ) for prompt in prompts]
        
#         responses = []
#         for i in range(0, len(texts), batch_size):
#             model_inputs = self.tokenizer(texts[i: i + batch_size], return_tensors="pt", truncation=True, padding=True).to(self.model.device)
#             if sample:
#                 model_inputs["do_sample"] = True
#                 model_inputs["temperature"] = 2.0
#                 model_inputs["top_p"] = 0.8
                
#             generated_ids = self.model.generate(
#                 **model_inputs,
#                 max_new_tokens=512
#             )
#             generated_ids = [
#                 output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
#             ]
            
#             for response in self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True):
#                 responses.append(response)
                
#         return responses

def Agent(model=None, _type: str=None):
    """
    Create an agent with the specified model or the default model
    
    Args:
        model: Model name or path (if None, uses DEFAULT_MODEL)
        
    Returns:
        An instance of BaseAgent
    """
    model = model or DEFAULT_MODEL
    
    if model.startswith("/") or model.startswith("./") or "checkpoint" in model:
        # return LocalAgent(model)
        pass
    else:
        return APIAgent(model, _type)
    
    
if __name__ == "__main__":
    agent = Agent()  # Uses DEFAULT_MODEL
    prompt = "Show me papers of reinforcement learning with LLM."
    print(agent.infer_score([prompt]))
