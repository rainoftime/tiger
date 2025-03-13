# Tiger Compiler Web UI

A web-based user interface for the Tiger compiler, allowing users to write, upload, and compile Tiger programs while viewing the intermediate steps of the compilation process.

## Features

- Write Tiger programs in a syntax-highlighted editor
- Upload existing Tiger programs
- Select from built-in example programs
- Compile Tiger programs and view the results of each compilation phase:
  - Lexical analysis
  - Abstract Syntax Tree (AST) visualization
  - Parsing
  - Semantic analysis
  - Intermediate representation (IR)
  - Canonized IR
  - Assembly code generation
  - Register allocation
  - Final assembly output

## Setup

1. Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
pip install flask
```

2. Run the web UI:

```bash
cd web_ui
python app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Write a Tiger program in the editor, or select an example from the dropdown menu, or upload a `.tig` file.
2. Click the "Compile" button to compile the program.
3. View the results of each compilation phase in the tabs on the right side.
4. Explore the AST visualization by clicking on nodes to expand or collapse subtrees.
5. If there are any errors during compilation, they will be displayed in the corresponding tab.

## AST Visualization

The AST visualization feature allows you to see the structure of your Tiger program as a tree. Each node in the tree represents a part of your program, such as a variable declaration, function call, or expression.

- Click on a node to expand or collapse its children
- Hover over a node to see more details
- Use the mouse wheel to zoom in and out
- Click and drag to pan around the visualization

## Examples

The web UI includes a variety of example Tiger programs from the `examples` directory. These examples demonstrate different features of the Tiger language and can be used as a starting point for writing your own programs.

## Development

- The web UI is built using Flask for the backend and modern web technologies for the frontend.
- The editor uses CodeMirror with a custom mode for Tiger syntax highlighting.
- The AST visualization uses D3.js to create an interactive tree diagram.
- The compilation process is handled by the existing Tiger compiler code.

## License

This project is licensed under the same license as the Tiger compiler. 