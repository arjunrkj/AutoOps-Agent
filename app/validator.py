"""
HCL Syntax Validation Module.
Checks bracket matching and block integrity for Terraform HCL code.
"""

def validate_hcl_syntax(hcl_text: str) -> bool:
    """
    Validates Terraform HCL syntax by verifying matching braces ({}) 
    and non-empty block definitions.
    Returns True if valid, False otherwise.
    """
    if not hcl_text or not hcl_text.strip():
        return False
        
    stack = []
    block_count = 0
    
    for char in hcl_text:
        if char == '{':
            stack.append('{')
            block_count += 1
        elif char == '}':
            if not stack:
                return False  # Unmatched closing brace
            stack.pop()
            
    # Check if all braces were properly closed and at least one block was parsed
    return len(stack) == 0 and block_count > 0
