import gradio as gr

def hello(name: str) -> str:
    return f"Hello, {name or 'world'} 👋"

demo = gr.Interface(fn=hello, inputs="text", outputs="text", title="OC5 Gradio Hello")

if __name__ == "__main__":
    demo.launch()
