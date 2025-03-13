import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import sys
import io
from contextlib import redirect_stdout

# Add the parent directory to the path so we can import the Tiger compiler modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from activation_records.frame import TempMap, sink, assembly_procedure
from activation_records.instruction_removal import is_redundant_move
from canonical.canonize import canonize
from intermediate_representation.fragment import FragmentManager, ProcessFragment, StringFragment
from register_allocation.allocation import RegisterAllocator
from semantic_analysis.analyzers import SemanticError, translate_program
from instruction_selection.codegen import Codegen
from putting_it_all_together.file_handler import FileHandler
from lexer import lex as le
from parser import parser as p
from ply import lex

app = Flask(__name__)

# Directory containing example Tiger programs
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16 KB max upload size

def get_example_files():
    """Get a list of example Tiger programs."""
    examples = []
    for filename in os.listdir(EXAMPLES_DIR):
        if filename.endswith('.tig'):
            examples.append(filename)
    return sorted(examples)

def get_example_content(filename):
    """Get the content of an example Tiger program."""
    with open(os.path.join(EXAMPLES_DIR, filename), 'r') as f:
        return f.read()

def compile_tiger_program(code):
    """Compile a Tiger program and return the results of each step."""
    results = {}
    
    # Reset the fragment manager
    FragmentManager.reset()
    
    # Capture stdout for each step
    lexer_output = io.StringIO()
    parser_output = io.StringIO()
    semantic_output = io.StringIO()
    ir_output = io.StringIO()
    canon_ir_output = io.StringIO()
    assembly_output = io.StringIO()
    regalloc_output = io.StringIO()
    
    try:
        # Lexical Analysis
        with redirect_stdout(lexer_output):
            lex.input(code)
            tokens = []
            while True:
                tok = lex.token()
                if not tok:
                    break
                tokens.append(str(tok))
            results['lexer'] = {'success': True, 'output': tokens}
        
        # Parsing
        try:
            with redirect_stdout(parser_output):
                parsed_program = p.parser.parse(code, le.lexer)
                results['parser'] = {'success': True, 'output': str(parsed_program)}
        except p.SyntacticError as err:
            results['parser'] = {'success': False, 'error': str(err)}
            return results
        
        # Semantic Analysis
        TempMap.initialize()
        try:
            with redirect_stdout(semantic_output):
                typed_exp = translate_program(parsed_program)
                results['semantic'] = {'success': True, 'output': str(typed_exp)}
        except SemanticError as err:
            results['semantic'] = {'success': False, 'error': str(err)}
            return results
        
        # IR Processing
        process_fragments = []
        string_fragments = []
        
        for fragment in FragmentManager.get_fragments():
            if isinstance(fragment, ProcessFragment):
                process_fragments.append(fragment)
            elif isinstance(fragment, StringFragment):
                string_fragments.append(fragment)
        
        with redirect_stdout(ir_output):
            from persistence.ir_dump import print_ir_list
            print_ir_list([fragment.body for fragment in process_fragments])
            ir_str = "\n".join([str(fragment.body) for fragment in process_fragments])
            results['ir'] = {'success': True, 'output': ir_output.getvalue() + "\n" + ir_str}
        
        # Canonization
        canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]
        
        with redirect_stdout(canon_ir_output):
            from persistence.ir_dump import print_canonized_ir
            print_canonized_ir(canonized_bodies)
            canon_ir_str = str(canonized_bodies)
            results['canon_ir'] = {'success': True, 'output': canon_ir_output.getvalue() + "\n" + canon_ir_str}
        
        # Instruction Selection
        assembly_bodies = [Codegen.codegen(process_body) for process_body in canonized_bodies]
        
        with redirect_stdout(assembly_output):
            assembly_str = str(assembly_bodies)
            results['assembly'] = {'success': True, 'output': assembly_str}
        
        # Create a temporary file for the output assembly
        with tempfile.NamedTemporaryFile(delete=False, suffix='.s') as temp_file:
            file_handler = FileHandler(temp_file.name)
            file_handler.print_data_header()
            for string_fragment in string_fragments:
                file_handler.print_string_fragment(string_fragment)
            
            file_handler.print_code_header()
            
            # Register Allocation
            bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]
            for body, fragment in zip(bodies_with_sink, process_fragments):
                allocation_result = RegisterAllocator(fragment.frame).main(body)
                TempMap.update_temp_to_register(allocation_result.temp_to_register)
                instruction_list = [
                    instruction
                    for instruction in allocation_result.instructions
                    if not is_redundant_move(instruction)
                ]
                procedure = assembly_procedure(fragment.frame, instruction_list)
                file_handler.print_assembly_procedure(procedure)
            
            with redirect_stdout(regalloc_output):
                regalloc_str = str(file_handler)
                results['regalloc'] = {'success': True, 'output': regalloc_str}
            
            # Read the generated assembly file
            with open(temp_file.name, 'r') as f:
                results['final_assembly'] = {'success': True, 'output': f.read()}
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
    except Exception as e:
        # Catch any other exceptions
        results['error'] = {'message': str(e)}
    
    return results

def extract_ast_data(parsed_program):
    """Extract AST data in a format suitable for visualization."""
    # This is a recursive function to convert the AST to a JSON-serializable format
    def convert_node(node):
        if node is None:
            return None
        
        # Get the class name as the node type
        node_type = node.__class__.__name__
        
        # Create a basic node structure
        result = {
            "type": node_type,
            "children": []
        }
        
        # Add attributes based on node type
        if hasattr(node, '__dict__'):
            for key, value in node.__dict__.items():
                # Skip private attributes
                if key.startswith('_'):
                    continue
                
                # Handle different types of values
                if isinstance(value, list):
                    # For lists, convert each item
                    children = []
                    for item in value:
                        child = convert_node(item)
                        if child:
                            children.append(child)
                    if children:
                        child_node = {
                            "type": key,
                            "children": children
                        }
                        result["children"].append(child_node)
                elif hasattr(value, '__dict__') or isinstance(value, tuple):
                    # For objects or tuples, convert recursively
                    child = convert_node(value)
                    if child:
                        child["type"] = f"{key}: {child['type']}"
                        result["children"].append(child)
                else:
                    # For primitive values, add as attribute
                    result[key] = str(value)
        
        return result
    
    # Start the conversion from the root
    return convert_node(parsed_program)

@app.route('/')
def index():
    examples = get_example_files()
    return render_template('index.html', examples=examples)

@app.route('/get_example/<filename>')
def get_example(filename):
    content = get_example_content(filename)
    return jsonify({'content': content})

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.form.get('code', '')
    results = compile_tiger_program(code)
    return jsonify(results)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and file.filename.endswith('.tig'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Clean up the uploaded file
        os.unlink(filepath)
        
        return jsonify({'content': content})
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/get_ast', methods=['POST'])
def get_ast():
    """Get the AST for a Tiger program."""
    code = request.form.get('code', '')
    
    try:
        # Parse the program
        parsed_program = p.parser.parse(code, le.lexer)
        
        # Extract AST data
        ast_data = extract_ast_data(parsed_program)
        
        return jsonify({'success': True, 'ast': ast_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 