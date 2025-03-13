// AST Visualizer for Tiger Compiler Web UI

class ASTVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.margin = { top: 20, right: 90, bottom: 30, left: 90 };
        this.width = 800 - this.margin.left - this.margin.right;
        this.height = 500 - this.margin.top - this.margin.bottom;
        this.nodeRadius = 5;
        this.duration = 750; // Animation duration
        this.i = 0; // Counter for node IDs
        this.tree = d3.tree().size([this.height, this.width]);
        this.diagonal = d3.linkHorizontal()
            .x(d => d.y)
            .y(d => d.x);
    }

    // Initialize the visualization
    initialize() {
        // Clear any existing SVG
        d3.select(`#${this.containerId}`).selectAll("*").remove();

        // Create SVG container
        this.svg = d3.select(`#${this.containerId}`).append("svg")
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom)
            .append("g")
            .attr("transform", `translate(${this.margin.left},${this.margin.top})`);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {
                this.svg.attr("transform", event.transform);
            });

        d3.select(`#${this.containerId} svg`)
            .call(zoom)
            .on("dblclick.zoom", null);

        // Add a message when no data is available
        this.svg.append("text")
            .attr("x", this.width / 2)
            .attr("y", this.height / 2)
            .attr("text-anchor", "middle")
            .text("Compile a program to see AST visualization.");
    }

    // Update the visualization with new data
    update(data) {
        // Clear any existing SVG
        d3.select(`#${this.containerId}`).selectAll("*").remove();

        // Create SVG container with zoom capability
        const svg = d3.select(`#${this.containerId}`).append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", `0 0 ${this.width + this.margin.left + this.margin.right} ${this.height + this.margin.top + this.margin.bottom}`)
            .attr("preserveAspectRatio", "xMidYMid meet");

        const g = svg.append("g")
            .attr("transform", `translate(${this.margin.left},${this.margin.top})`);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });

        svg.call(zoom)
            .on("dblclick.zoom", null);

        // Assigns parent, children, height, depth
        this.root = d3.hierarchy(data, d => d.children);
        this.root.x0 = this.height / 2;
        this.root.y0 = 0;

        // Compute the new tree layout
        const nodes = this.tree(this.root);
        const links = nodes.links();

        // Normalize for fixed-depth
        nodes.descendants().forEach(d => {
            d.y = d.depth * 180;
        });

        // Update the nodes
        const node = g.selectAll(".node")
            .data(nodes.descendants(), d => d.id || (d.id = ++this.i));

        // Enter new nodes at the parent's previous position
        const nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.y},${d.x})`)
            .on("click", (event, d) => {
                // Toggle children on click
                if (d.children) {
                    d._children = d.children;
                    d.children = null;
                } else {
                    d.children = d._children;
                    d._children = null;
                }
                this.update(data);
            });

        // Add Circle for the nodes
        nodeEnter.append("circle")
            .attr("r", this.nodeRadius)
            .style("fill", d => d._children ? "#add8e6" : "#fff")
            .style("stroke", "steelblue")
            .style("stroke-width", "1.5px");

        // Add labels for the nodes
        nodeEnter.append("text")
            .attr("dy", ".35em")
            .attr("x", d => d.children || d._children ? -13 : 13)
            .attr("text-anchor", d => d.children || d._children ? "end" : "start")
            .text(d => d.data.type)
            .style("font-size", "12px");

        // Add tooltips for node details
        nodeEnter.append("title")
            .text(d => {
                let tooltip = `Type: ${d.data.type}\n`;
                // Add other properties
                Object.entries(d.data).forEach(([key, value]) => {
                    if (key !== "type" && key !== "children") {
                        tooltip += `${key}: ${value}\n`;
                    }
                });
                return tooltip;
            });

        // Update the links
        const link = g.selectAll(".link")
            .data(links, d => d.target.id);

        // Enter any new links at the parent's previous position
        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", d => {
                return this.diagonal(d);
            })
            .style("fill", "none")
            .style("stroke", "#ccc")
            .style("stroke-width", "1.5px");
    }
}

// Initialize the visualizer when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.astVisualizer = new ASTVisualizer('ast-tree');
    window.astVisualizer.initialize();
}); 