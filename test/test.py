import os
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl, wlexpr

KERNEL_PATH = r"D:\Program Files\Wolfram Research\Wolfram\14.2\WolframKernel.exe"



def latex_to_mathematica(latex_str):
    """将 LaTeX 转换为 Mathematica 表达式"""
    try:
        # 直接指定内核路径
        kernel_path = r"D:\Program Files\Wolfram Research\Wolfram\14.2\WolframKernel.exe"
        
        with WolframLanguageSession(kernel=kernel_path) as session:
            # 构建转换表达式
            expr = f'ToExpression["{latex_str}", TeXForm]'
            result = session.evaluate(expr)
            return result
    except Exception as e:
        print(f"转换失败: {e}")
        return None


# 测试转换
latex_expr = r"\\frac{\\sin (x)+\\cos (x)}{\\sqrt[3]{\\sin (x)-\\cos (x)}}"
result = latex_to_mathematica(latex_expr)
print("转换结果:", result)

# 单独的会话测试
with WolframLanguageSession(kernel=KERNEL_PATH) as session:
    res = session.evaluate(wl.Factorial(10))
    print("10! =", res)

# 确保程序退出
print("所有操作完成，程序将退出")