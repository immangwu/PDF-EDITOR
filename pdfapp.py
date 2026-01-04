import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from PIL import Image
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas

# Page configuration
st.set_page_config(
    page_title="Interactive PDF Editor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    .stApp {
        background: transparent;
    }
    .editor-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .header-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .header-subtitle {
        font-size: 1.3rem;
        color: #4a5568;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    .tool-card {
        background: #f7fafc;
        border-radius: 12px;
        padding: 1.5rem;
        border: 2px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'pdf_image' not in st.session_state:
    st.session_state.pdf_image = None
if 'canvas_result' not in st.session_state:
    st.session_state.canvas_result = None
if 'text_annotations' not in st.session_state:
    st.session_state.text_annotations = []

def pdf_page_to_image(pdf_file, page_num, zoom=2):
    """Convert PDF page to image"""
    pdf_file.seek(0)
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    page = pdf_document[page_num]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    return img, pix.width, pix.height

# Header
st.markdown('<div class="editor-container">', unsafe_allow_html=True)
st.markdown('<div class="header-title">📝 Interactive PDF Editor</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Draw directly on your PDF - Click, Draw, Save!</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 Drawing Tools")
    
    drawing_mode = st.selectbox(
        "Select Tool:",
        ["freedraw", "line", "rect", "circle", "transform", "point"],
        format_func=lambda x: {
            "freedraw": "✏️ Free Draw",
            "line": "📏 Line",
            "rect": "⬜ Rectangle",
            "circle": "⭕ Circle",
            "transform": "↔️ Transform",
            "point": "📍 Point"
        }[x]
    )
    
    st.markdown("---")
    st.markdown("## 🎨 Style Settings")
    
    stroke_width = st.slider("Pen Width", 1, 25, 3)
    stroke_color = st.color_picker("Pen Color", "#000000")
    fill_color = st.color_picker("Fill Color", "#FFFF00")
    
    st.markdown("---")
    st.markdown("## 📝 Text Tool")
    
    if st.button("➕ Add Text Annotation", use_container_width=True):
        st.session_state.adding_text = True
    
    if 'adding_text' in st.session_state and st.session_state.adding_text:
        text_input = st.text_input("Enter text:", key="text_input")
        
        font_family = st.selectbox(
            "Font Family:",
            ["Helvetica", "Helvetica-Bold", "Courier", "Courier-Bold", "Times-Roman", "Times-Bold"]
        )
        
        font_size = st.slider("Font Size:", 8, 72, 14)
        text_color = st.color_picker("Text Color:", "#000000")
        
        col1, col2 = st.columns(2)
        with col1:
            text_x = st.number_input("X Position:", 0, 1000, 100)
        with col2:
            text_y = st.number_input("Y Position:", 0, 1000, 100)
        
        if st.button("✅ Add Text", use_container_width=True):
            if text_input:
                st.session_state.text_annotations.append({
                    'text': text_input,
                    'font': font_family,
                    'size': font_size,
                    'color': text_color,
                    'x': text_x,
                    'y': text_y,
                    'page': st.session_state.current_page
                })
                st.session_state.adding_text = False
                st.success("✅ Text added!")
                st.rerun()
    
    if st.session_state.text_annotations:
        st.markdown(f"**Text Annotations:** {len(st.session_state.text_annotations)}")
        if st.button("🗑️ Clear Text Annotations", use_container_width=True):
            st.session_state.text_annotations = []
            st.rerun()
    
    st.markdown("---")
    
    bg_option = st.checkbox("Show PDF Background", value=True)
    
    st.markdown("---")
    st.markdown("## 💡 Instructions")
    st.info("""
    1. Upload your PDF
    2. Select a drawing tool
    3. Draw directly on the PDF
    4. Add text with fonts
    5. Click 'Save PDF' to download
    """)

# Main content
uploaded_file = st.file_uploader("📤 Upload PDF File", type=['pdf'])

if uploaded_file:
    st.session_state.pdf_file = uploaded_file
    
    # Read PDF info
    pdf_reader = PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)
    
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.metric("Total Pages", num_pages)
    
    with col2:
        if num_pages > 1:
            st.session_state.current_page = st.selectbox(
                "Select Page:",
                range(num_pages),
                format_func=lambda x: f"Page {x + 1}"
            )
    
    with col3:
        st.metric("Current Page", st.session_state.current_page + 1)
    
    st.markdown("---")
    
    # Convert current page to image
    pdf_img, img_width, img_height = pdf_page_to_image(
        uploaded_file, 
        st.session_state.current_page,
        zoom=2
    )
    st.session_state.pdf_image = pdf_img
    
    # Create two columns for canvas and preview
    canvas_col, preview_col = st.columns([3, 2])
    
    with canvas_col:
        st.markdown("### 🎨 Draw on PDF")
        
        # Drawing canvas
        canvas_result = st_canvas(
            fill_color=fill_color + "80",  # Add transparency
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color="#ffffff" if not bg_option else None,
            background_image=pdf_img if bg_option else None,
            update_streamlit=True,
            height=img_height,
            width=img_width,
            drawing_mode=drawing_mode,
            point_display_radius=stroke_width,
            key="canvas",
        )
        
        st.session_state.canvas_result = canvas_result
    
    with preview_col:
        st.markdown("### 👁️ Annotations Preview")
        
        if st.session_state.text_annotations:
            st.markdown(f"**Text Elements:** {len(st.session_state.text_annotations)}")
            for i, text_ann in enumerate(st.session_state.text_annotations):
                if text_ann['page'] == st.session_state.current_page:
                    with st.expander(f"Text {i+1}: {text_ann['text'][:20]}..."):
                        st.write(f"**Font:** {text_ann['font']}")
                        st.write(f"**Size:** {text_ann['size']}px")
                        st.write(f"**Position:** ({text_ann['x']}, {text_ann['y']})")
                        if st.button(f"🗑️ Delete", key=f"del_text_{i}"):
                            st.session_state.text_annotations.pop(i)
                            st.rerun()
        
        if canvas_result.image_data is not None:
            st.image(canvas_result.image_data, caption="Drawing Preview", use_container_width=True)
    
    st.markdown("---")
    
    # Save button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save Edited PDF", use_container_width=True, type="primary"):
            with st.spinner("Processing your PDF..."):
                try:
                    uploaded_file.seek(0)
                    pdf_reader = PdfReader(uploaded_file)
                    pdf_writer = PdfWriter()
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        page_width = float(page.mediabox.width)
                        page_height = float(page.mediabox.height)
                        
                        # Create overlay
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                        
                        # Add text annotations for this page
                        for text_ann in st.session_state.text_annotations:
                            if text_ann['page'] == page_num:
                                can.setFont(text_ann['font'], text_ann['size'])
                                can.setFillColor(HexColor(text_ann['color']))
                                # Convert coordinates (canvas uses bottom-left origin)
                                y_converted = page_height - text_ann['y']
                                can.drawString(text_ann['x'], y_converted, text_ann['text'])
                        
                        # Add canvas drawings for this page
                        if page_num == st.session_state.current_page and canvas_result.image_data is not None:
                            # Convert canvas drawing to image
                            canvas_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                            
                            # Scale image to PDF size
                            scale_x = page_width / img_width
                            scale_y = page_height / img_height
                            
                            # Save canvas image temporarily
                            img_buffer = io.BytesIO()
                            canvas_img.save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            
                            # Draw on canvas (scaled)
                            can.drawImage(
                                img_buffer,
                                0, 0,
                                width=page_width,
                                height=page_height,
                                mask='auto'
                            )
                        
                        can.save()
                        
                        # Merge overlay
                        packet.seek(0)
                        overlay = PdfReader(packet)
                        page.merge_page(overlay.pages[0])
                        pdf_writer.add_page(page)
                    
                    # Save to bytes
                    output = io.BytesIO()
                    pdf_writer.write(output)
                    output.seek(0)
                    
                    st.success("✅ PDF edited successfully!")
                    
                    st.download_button(
                        label="⬇️ Download Edited PDF",
                        data=output,
                        file_name="edited_pdf.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

else:
    st.info("👆 Please upload a PDF file to start editing")
    
    # Show demo features
    st.markdown("### ✨ Features")
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
        #### 🎨 Drawing Tools
        - Free hand drawing
        - Lines and arrows
        - Rectangles
        - Circles
        - Points
        """)
    
    with cols[1]:
        st.markdown("""
        #### 📝 Text Tools
        - Multiple fonts
        - Custom sizes
        - Color selection
        - Precise positioning
        - Bold & Regular
        """)
    
    with cols[2]:
        st.markdown("""
        #### 💾 Export
        - Save as PDF
        - Keep quality
        - Multi-page support
        - Easy download
        """)

st.markdown('</div>', unsafe_allow_html=True)
