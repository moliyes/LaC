import re
import sympy as sp
from sympy import Integral, Eq, I, pi, exp, Function, Lambda
from sympy.core.relational import Relational
from latex2sympy2_extended.logic import And
import numpy as np
from math_verify import parse, verify, LatexExtractionConfig



def compute_score(data_source:str,
    solution_str, ground_truth, extra_info=None,
):
    score = 0.0
    acc = False
    pred = ground_truth

    if data_source == "theoretical_physics":
        print("theoretical physics problem")
    
    print("--------------------------------")
    print("Ground truth: ", ground_truth)
    print("Solution: ", solution_str)

    try:
        string_in_last_boxed = last_boxed_only_string(solution_str)     #提取最后一个box的字符
        if string_in_last_boxed is not None:
            answer = remove_boxed(string_in_last_boxed) #提取答案
            if data_source == "theoretical_physics":
                answer = answer_refine(answer)
                ground_truth = answer_refine(ground_truth)  
                is_correct = is_equiv_TP(answer, ground_truth, verbose=True)
                if is_correct:
                    score = 1.0
                    print("------------CORRECT-------------")
                    acc = True
                else:
                    print("------------WRONG-------------")
                    score = 0.1
        else:
            print("------------FORMAT ERROR-------------")
            score = 0.0
    except Exception as e:
        print(e)
        score = 0.0

    return {
        "score": score,
        "acc": acc,
        "pred": pred,
    }


def is_equiv_TP(answer_str, truth_str, verbose=False) -> bool:   #验证核心逻辑
    if answer_str is None and truth_str is None:    
        print("WARNING: Both None")
        return True
    if answer_str is None or truth_str is None:
        return False
    
    truth = parse(truth_str, extraction_mode='first_match', extraction_config=[LatexExtractionConfig()])
    if len(truth) != 2:
        truth = parse(truth_str)
    
    answer = parse(answer_str, extraction_mode='first_match', extraction_config=[LatexExtractionConfig()])

    if len(answer) != 2:
        answer = parse(answer_str)
        if len(answer) != 2:
            return False  
            
    if is_equation(answer[0]):   #检查是否为方程
        answer[0] = take_last_relation(answer[0]).rhs
        # answer[0] = take_last_relation(answer[0])

    if verbose:
        print("Sympy Expr (Answer): ", answer[0])
        print("Sympy Expr (Truth):  ", truth[0])
    return verify(answer[0], truth[0])



def is_equation(expr) -> bool:
    """Check if an expression is an equation.

    Args:
        expr: The expression to check
    Returns:
        bool: True if expr is an equation, False otherwise
    """
    if isinstance(expr, Eq):
        return True

    if isinstance(expr, And) and len(expr._unsorted_args) > 0:
        return all(isinstance(arg, Eq) for arg in expr._unsorted_args)

    return False

def take_last_relation(expr: And | Relational) -> Relational:
    """Take the last relation from an And expression.""" #从And表达式中取出最后一个关系式（等式）
    if isinstance(expr, And):
        return take_last_relation(expr._unsorted_args[-1])
    return expr

def answer_refine(text):  #LaTeX格式标准化
    text = text.replace("\n","")
    text = text.strip()
    pattern = re.compile(r'^(\$|\\\(|\\\[)')
    if not bool(pattern.match(text)):
        text = r"\[" + text + r"\]"
    return text  

def extract_boxed_content(s: str) -> str: #提取boxed内容，处理嵌套花括号
    """
    Extract the content inside the first \boxed{} LaTeX command, handling nested braces.
    
    Args:
        s (str): Input string containing the boxed expression
        
    Returns:
        str: The content inside the boxed braces, or empty string if not found
    """
    # Find the start of the \boxed{ command
    start = s.find(r'\boxed{')
    if start == -1:
        return ""
    
    # Position after the opening '{' of \boxed
    content_start = start + len(r'\boxed{')
    balance = 1  # Start with 1 because we've already encountered the opening '{'
    end_pos = None
    
    # Iterate to find the matching closing '}'
    for i in range(content_start, len(s)):
        char = s[i]
        if char == '{':
            balance += 1
        elif char == '}':
            balance -= 1
        if balance == 0:
            end_pos = i
            break
    
    if end_pos is None:
        return ""  # No closing brace found
    
    return s[content_start:end_pos]

def remove_boxed(text):
    if "\\boxed{" in text:
        return extract_boxed_content(text)
    else:
        return text


def last_boxed_only_string(string):
    idx = string.rfind("\\boxed")
    if "\\boxed " in string:
        return "\\boxed " + string.split("\\boxed ")[-1].split("$")[0]
    if idx < 0:
        idx = string.rfind("\\fbox")
        if idx < 0:
            return None

    i = idx
    right_brace_idx = None
    num_left_braces_open = 0
    while i < len(string):
        if string[i] == "{":
            num_left_braces_open += 1
        if string[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break
        i += 1

    if right_brace_idx is None:
        retval = None
    else:
        retval = string[idx : right_brace_idx + 1]

    return retval

def test_answer(answer_str):
    string_in_last_boxed = last_boxed_only_string(answer_str)
    if string_in_last_boxed is not None:
        extracted_answer = extract_boxed_content(string_in_last_boxed)
    else:
        print("No boxed content found in the answer string.")
        return None
    refined_answer = answer_refine(extracted_answer)

    answer = parse(refined_answer, extraction_mode='first_match', extraction_config=[LatexExtractionConfig()])

    if len(answer) != 2:
        print("not parse LaTex string!")
        return False
    
    # print("Sympy Expr (Answer): ", answer[0])
    if is_equation(answer[0]):
        answer[0] = take_last_relation(answer[0]).rhs

    print("Sympy Expr (Answer): ", answer[0])
    return True





if __name__ == "__main__":
    # answer = "The static longitudinal dielectric function $\\epsilon(q, 0)$ for a free electron gas at zero temperature, within the random phase approximation, is given by the Lindhard formula. The final expression, in terms of the wave vector $q$, the Fermi wave vector $k_F$, and the Thomas-Fermi screening wave vector $k_{TF}$, is:\n$$ \\boxed{ \\epsilon(q, 0) = 1 + \\frac{k_{TF}^2}{q^2} \\left[ \\frac{1}{2} + \\frac{4k_F^2 - q^2}{8k_F q} \\ln \\left| \\frac{2k_F+q}{2k_F-q} \\right| \\right] } $$"
    # answer_1 = "\n\\[\n\\boxed{\\epsilon(q,0) = 1 + \\dfrac{k_{TF}^{2}}{q^{2}} \\left( \\dfrac{1}{2} + \\dfrac{4k_{F}^{2} - q^{2}}{8k_{F} q} \\ln \\left| \\dfrac{2k_{F} + q}{2k_{F} - q} \\right| \\right)}\n\\]"

    # answer_2 = "\nThe critical temperature is:  \n$$  \n\\boxed{1.13 \\frac{\\hbar \\omega_D}{k_B} \\exp\\left(-\\dfrac{1}{\\lambda}\\right)}  \n$$  \n"
    # answer_3 = "\nThe exchange energy per particle is given by the expression:\n$$\n\\boxed{-\\dfrac{3e^{2}}{4} \\left( \\dfrac{3}{\\pi} \\right)^{\\!\\!1/3} n^{1/3}}\n$$\n"
    
    answer_0 = r"\boxed{a^\dagger a}"
    # answer_1 = r"\frac{t}{U} = \frac{1}{z} \frac{\frac{\mu}{U}\left(1-\frac{\mu}{U}\right)}{1+\frac{\mu}{U}}"
    # answer_2 = r"\[\boxed{T_c = \frac{J z}{k_B}}\]"
    # answer_3 = r""
    # print(answer_0)
    test_answer(answer_0)

    # data_source = "theoritical_physics"
    # reward_metric = compute_score(data_source, answer_2, answer_3)
    # print(reward_metric["acc"])
