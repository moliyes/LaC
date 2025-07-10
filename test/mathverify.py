import json
import os
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl
import concurrent.futures # If we decide to use multiprocessing

class MathVerifier:
    def __init__(self, kernel_path):
        self.kernel_path = kernel_path
        self.session = None # 将 session 初始化为 None

    def __enter__(self):
        # 在进入上下文时创建并启动 WolframLanguageSession
        try:
            self.session = WolframLanguageSession(kernel=self.kernel_path)
            self.session.__enter__() # 调用 session 的 __enter__ 方法
            print("WolframLanguageSession started.")
        except Exception as e:
            print(f"Failed to start WolframLanguageSession: {e}")
            self.session = None # 确保 session 为 None 如果启动失败
            raise # 重新抛出异常，阻止程序继续执行
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 在退出上下文时关闭 WolframLanguageSession
        if self.session:
            self.session.__exit__(exc_type, exc_val, exc_tb)
            print("WolframLanguageSession closed.")
        
    def latex_to_mathematica(self, latex_str):
        """将 LaTeX 转换为 Mathematica 表达式"""
        if not self.session:
            print("Error: WolframLanguageSession is not active.")
            return None
        try:
            # 直接传递 latex_str，wolframclient 会处理转义
            # 使用 HoldForm 保持表达式结构，同时允许 ToExpression 解析 TeXForm
            expr = wl.ToExpression(latex_str, wl.TeXForm)
            # 评估表达式，得到 Mathematica 表达式的字符串表示
            result = self.session.evaluate(expr)
            # result 是一个 WolframLanguage 表达式对象，需要转换成 string
            return str(result)
        except Exception as e:
            print(f"LaTeX 转换失败: '{latex_str}'\n错误: {str(e)}")
            return None
                
    def is_equivalent(self, expr1, expr2, variable='x'):
        """
        检查两个表达式是否为同一个不定积分的结果，即它们的导数是否相等。
        
        Args:
            expr1 (str): 第一个 Mathematica 表达式的字符串表示。
            expr2 (str): 第二个 Mathematica 表达式的字符串表示。
            variable (str): 积分变量的符号，默认为 'x'。
            
        Returns:
            bool: 如果两个表达式的导数相等，则返回 True，否则返回 False。
        """
        if not self.session:
            print("Error: WolframLanguageSession is not active for is_integral_equivalent.")
            return False
            
        if not expr1 or not expr2 or not isinstance(expr1, str) or not isinstance(expr2, str):
            print(f"Error: Invalid integral expressions provided. expr1='{expr1}', expr2='{expr2}'")
            return False
        try:
            # 将变量字符串转换为 Wolfram Language Symbol 对象
            sym_variable = wl.Symbol(variable)
            # 评估表达式字符串为 Wolfram Language 表达式对象
            parsed_expr1 = wl.ToExpression(expr1)
            parsed_expr2 = wl.ToExpression(expr2)
            # 计算两个表达式的导数
            deriv_expr1 = wl.D(parsed_expr1, sym_variable)
            deriv_expr2 = wl.D(parsed_expr2, sym_variable)
            # 再次使用 FullSimplify 检查这两个导数的差是否为 0
            # FullSimplify[deriv1 - deriv2 == 0] 或者 FullSimplify[deriv1 == deriv2]
            check_derivs_equality = wl.FullSimplify(wl.Equal(deriv_expr1, deriv_expr2))
            
            result = self.session.evaluate(check_derivs_equality)
            
            # 如果导数相等，FullSimplify 应该返回 True
            return result == True
        except Exception as e:
            print(f"Integral equivalence check failed for derivatives of '{expr1}' vs '{expr2}' (variable '{variable}').\n错误: {type(e).__name__}: {str(e)}")
            return False

                
    def process_test_case(self, test_case):
        """处理单个测试用例"""
        # 填充缺失的 Mathematica 表达式
        if test_case["input"]["mathematica"] is None:
            # Check if latex exists before attempting conversion
            if "latex" not in test_case["input"] or test_case["input"]["latex"] is None:
                print(f"Warning: Missing 'latex' for input expression in test case: {test_case.get('id', 'N/A')}")
                test_case["result"] = "conversion_failed"
                return test_case
            test_case["input"]["mathematica"] = self.latex_to_mathematica(
                test_case["input"]["latex"]
            )
            
        if test_case["reference"]["mathematica"] is None:
            # Check if latex exists before attempting conversion
            if "latex" not in test_case["reference"] or test_case["reference"]["latex"] is None:
                print(f"Warning: Missing 'latex' for reference expression in test case: {test_case.get('id', 'N/A')}")
                test_case["result"] = "conversion_failed"
                return test_case
            test_case["reference"]["mathematica"] = self.latex_to_mathematica(
                test_case["reference"]["latex"]
            )
        
        # 检查是否转换成功 (只要有一个失败，就认为转换失败)
        if not test_case["input"]["mathematica"] or not test_case["reference"]["mathematica"]:
            test_case["result"] = "conversion_failed"
            return test_case
            
        # 检查等价性
        test_case["result"] = "correct" if self.is_equivalent(
            test_case["input"]["mathematica"],
            test_case["reference"]["mathematica"]
        ) else "incorrect"
        
        return test_case
        
    def batch_process(self, test_cases):
        """批量处理测试用例"""

        results = [self.process_test_case(tc) for tc in test_cases]
        return results
        
    def generate_report(self, results, output_file):
        """生成测试报告"""
        report = {
            "summary": {
                "total": len(results),
                "correct": sum(1 for r in results if r.get("result") == "correct"),
                "incorrect": sum(1 for r in results if r.get("result") == "incorrect"),
                "conversion_failed": sum(1 for r in results if r.get("result") == "conversion_failed")
            },
            "details": results
        }
        
        try:
            with open(output_file, "w", encoding="utf-8") as f: # 确保使用 utf-8 编码
                json.dump(report, f, indent=2, ensure_ascii=False) # allow non-ASCII characters
            print(f"Report generated successfully: {output_file}")
        except IOError as e:
            print(f"Error writing report to file {output_file}: {e}")
        return report

# 主程序
if __name__ == "__main__":
    # 配置
    KERNEL_PATH = r"D:\Program Files\Wolfram Research\Wolfram\14.2\WolframKernel.exe" 

    # 获取当前脚本所在目录
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # 构建输入输出文件的完整路径
    INPUT_FILE = os.path.join(SCRIPT_DIR, "t1.json")
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "verification_report.json")

    # 检查输入文件是否存在
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        exit(1)

    # 加载测试用例
    test_cases = []
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f: # 确保使用 utf-8 编码
            test_cases = json.load(f)
        print(f"Loaded {len(test_cases)} test cases from {INPUT_FILE}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {INPUT_FILE}: {e}")
        exit(1)
    except IOError as e:
        print(f"Error reading input file {INPUT_FILE}: {e}")
        exit(1)
    
    # 创建验证器并处理测试用例
    try:
        with MathVerifier(KERNEL_PATH) as verifier:
            if verifier.session: # 只有当会话成功启动时才继续
                # 直接调用 batch_process，它内部会处理转换和检查
                results = verifier.batch_process(test_cases)
                
                # 生成报告
                verifier.generate_report(results, OUTPUT_FILE)
            else:
                print("Skipping test case processing due to failed WolframLanguageSession startup.")
    except Exception as e:
        print(f"An error occurred during verification process: {e}")


