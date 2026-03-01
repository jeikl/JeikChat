from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI


# 初始化客户端
llm = ChatDeepSeek(
    api_base="https://ark.cn-beijing.volces.com/api/v3",
    api_key="6246ef67-931a-4f19-9409-89b42fc04a91",
    model="doubao-seed-2-0-pro-260215",
    streaming=True,
    timeout=1800,
)

llm2=ChatOpenAI(
    api_base="https://ark.cn-beijing.volces.com/api/v3",
    api_key="6246ef67-931a-4f19-9409-89b42fc04a91",
    model="doubao-seed-2-0-pro-260215",
    streaming=True,
    timeout=1800,
)



messages = [{"role": "user", "content": "介绍一下深度思考模型的特点"}]

print("=" * 20 + "思考过程" + "=" * 20)

# 智能推理内容处理器
class ReasoningProcessor:
    def __init__(self):
        self.current_reasoning = ""
        self.is_printing_answer = False
        self.reasoning_count = 0
        self.answer_count = 0
    
    def process_chunk(self, chunk):
        """处理单个 chunk，智能输出推理内容和标准内容"""
        
        # 处理推理内容
        reasoning_processed = self._process_reasoning_content(chunk)
        
        # 处理标准内容
        answer_processed = self._process_standard_content(chunk)
        
        return reasoning_processed, answer_processed
    
    def _process_reasoning_content(self, chunk):
        """处理推理内容"""
        if not hasattr(chunk, 'additional_kwargs') or not chunk.additional_kwargs:
            return False
        
        reasoning_content = chunk.additional_kwargs.get('reasoning_content')
        if not reasoning_content:
            return False
        
        # 累积推理内容
        self.current_reasoning += reasoning_content
        
        # 智能判断何时输出推理内容
        should_output = self._should_output_reasoning(reasoning_content)
        
        if should_output and self.current_reasoning.strip():
            # 在输出推理内容前确保格式正确
            if not self.is_printing_answer and self.reasoning_count == 0:
                print("\n推理过程：", end="", flush=True)
            
            print(self.current_reasoning, end="", flush=True)
            self.reasoning_count += 1
            self.current_reasoning = ""
            return True
        
        return False
    
    def _should_output_reasoning(self, current_content):
        """判断是否应该输出当前累积的推理内容"""
        # 基于标点符号判断句子结束
        sentence_enders = ['.', '。', '!', '！', '?', '？', ';', '；']
        
        # 如果当前内容是句子结束符
        if current_content in sentence_enders:
            return True
        
        # 如果累积内容过长（避免缓冲区过大）
        if len(self.current_reasoning) > 80:
            return True
        
        # 如果遇到换行符
        if '\n' in self.current_reasoning:
            return True
        
        return False
    
    def _process_standard_content(self, chunk):
        """处理标准内容"""
        if not chunk.content:
            return False
        
        # 如果是第一次输出答案内容
        if not self.is_printing_answer:
            # 先输出所有剩余的推理内容
            if self.current_reasoning.strip():
                if self.reasoning_count == 0:
                    print("\n推理过程：", end="", flush=True)
                print(self.current_reasoning, end="", flush=True)
                self.current_reasoning = ""
            
            print("\n" + "=" * 20 + "完整回复" + "=" * 20)
            self.is_printing_answer = True
        
        print(chunk.content, end="", flush=True)
        self.answer_count += 1
        return True
    
    def finalize(self):
        """处理最后剩余的内容"""
        # 输出最后剩余的推理内容
        if self.current_reasoning.strip():
            if not self.is_printing_answer and self.reasoning_count == 0:
                print("\n推理过程：", end="", flush=True)
            print(self.current_reasoning, end="", flush=True)
        
        print()
        
        # 输出统计信息
        print("\n" + "=" * 20 + "统计信息" + "=" * 20)
        print(f"推理步骤数: {self.reasoning_count}")
        print(f"回答内容块数: {self.answer_count}")
        print("推理内容已成功捕获并智能输出！")


# 使用智能处理器
processor = ReasoningProcessor()

print("开始流式处理...\n")

for chunk in llm.stream(messages):
    reasoning_processed, answer_processed = processor.process_chunk(chunk)

# 处理最后的内容
processor.finalize()

print("\n" + "=" * 20 + "处理完成" + "=" * 20)