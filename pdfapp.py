import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from PIL import Image
import fitz  # PyMuPDF for better PDF rendering

# Page configuration
st.set_page_config(
    page_title="Professional PDF Editor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .header-subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    .upload-section {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: white;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header-title">📄 Professional PDF Editor</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Edit, annotate, and enhance your PDF documents with ease</div>', unsafe_allow_html=True)

# Initialize session state
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None
if 'annotations' not in st.session_state:
    st.session_state.annotations = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

# Sidebar for tools and options
with st.sidebar:
    st.markdown("### 🛠️ Editing Tools")
    
    tool_option = st.radio(
        "Select Tool:",
        ["Add Text", "Add Shape", "Add Rectangle", "Add Circle", "Add Line", "Highlight"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Tool Settings")
    
    if tool_option == "Add Text":
        text_content = st.text_input("Text Content", "Sample Text")
        font_size = st.slider("Font Size", 8, 72, 14)
        text_color = st.color_picker("Text Color", "#000000")
        x_pos = st.slider("X Position", 0, 600, 100)
        y_pos = st.slider("Y Position", 0, 800, 700)
        
    elif tool_option in ["Add Rectangle", "Highlight"]:
        rect_width = st.slider("Width", 10, 500, 200)
        rect_height = st.slider("Height", 10, 300, 100)
        rect_x = st.slider("X Position", 0, 600, 100)
        rect_y = st.slider("Y Position", 0, 800, 600)
        fill_color = st.color_picker("Fill Color", "#FFD700" if tool_option == "Highlight" else "#FF0000")
        stroke_color = st.color_picker("Stroke Color", "#000000")
        opacity = st.slider("Opacity", 0.0, 1.0, 0.3 if tool_option == "Highlight" else 1.0, 0.1)
        
    elif tool_option == "Add Circle":
        circle_radius = st.slider("Radius", 10, 200, 50)
        circle_x = st.slider("Center X", 0, 600, 200)
        circle_y = st.slider("Center Y", 0, 800, 600)
        circle_fill = st.color_picker("Fill Color", "#0000FF")
        circle_stroke = st.color_picker("Stroke Color", "#000000")
        circle_opacity = st.slider("Opacity", 0.0, 1.0, 1.0, 0.1)
        
    elif tool_option == "Add Line":
        line_x1 = st.slider("Start X", 0, 600, 100)
        line_y1 = st.slider("Start Y", 0, 800, 600)
        line_x2 = st.slider("End X", 0, 600, 300)
        line_y2 = st.slider("End Y", 0, 800, 400)
        line_color = st.color_picker("Line Color", "#000000")
        line_width = st.slider("Line Width", 1, 10, 2)
    
    st.markdown("---")
    
    if st.button("➕ Add to PDF", use_container_width=True):
        annotation = {
            'type': tool_option,
            'page': st.session_state.current_page
        }
        
        if tool_option == "Add Text":
            annotation.update({
                'text': text_content,
                'font_size': font_size,
                'color': text_color,
                'x': x_pos,
                'y': y_pos
            })
        elif tool_option in ["Add Rectangle", "Highlight"]:
            annotation.update({
                'width': rect_width,
                'height': rect_height,
                'x': rect_x,
                'y': rect_y,
                'fill_color': fill_color,
                'stroke_color': stroke_color,
                'opacity': opacity
            })
        elif tool_option == "Add Circle":
            annotation.update({
                'radius': circle_radius,
                'x': circle_x,
                'y': circle_y,
                'fill_color': circle_fill,
                'stroke_color': circle_stroke,
                'opacity': circle_opacity
            })
        elif tool_option == "Add Line":
            annotation.update({
                'x1': line_x1,
                'y1': line_y1,
                'x2': line_x2,
                'y2': line_y2,
                'color': line_color,
                'width': line_width
            })
        
        st.session_state.annotations.append(annotation)
        st.success("✅ Annotation added!")
    
    if st.session_state.annotations:
        st.markdown(f"**Annotations:** {len(st.session_state.annotations)}")
        if st.button("🗑️ Clear All Annotations", use_container_width=True):
            st.session_state.annotations = []
            st.rerun()

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 📤 Upload PDF")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload the PDF you want to edit"
    )
    
    if uploaded_file:
        st.session_state.pdf_file = uploaded_file
        
        # Read PDF
        pdf_reader = PdfReader(uploaded_file)
        num_pages = len(pdf_reader.pages)
        
        st.success(f"✅ PDF loaded: {num_pages} page(s)")
        
        # Page selector
        if num_pages > 1:
            st.session_state.current_page = st.selectbox(
                "Select Page to Edit",
                range(num_pages),
                format_func=lambda x: f"Page {x + 1}"
            )
        
        # Preview current page
        st.markdown("### 👁️ PDF Preview")
        try:
            # Convert PDF page to image for preview using PyMuPDF
            uploaded_file.seek(0)
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            page = pdf_document[st.session_state.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            st.image(img, use_container_width=True, caption=f"Page {st.session_state.current_page + 1}")
        except Exception as e:
            st.warning("Preview not available. Please apply annotations to see results.")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 🎨 Annotation Preview")
    
    if st.session_state.annotations:
        st.markdown(f"**Total Annotations:** {len(st.session_state.annotations)}")
        
        # Group annotations by page
        page_annotations = {}
        for i, ann in enumerate(st.session_state.annotations):
            page = ann.get('page', 0)
            if page not in page_annotations:
                page_annotations[page] = []
            page_annotations[page].append((i, ann))
        
        # Display annotations for current page
        current_page_anns = page_annotations.get(st.session_state.current_page, [])
        
        if current_page_anns:
            st.markdown(f"**Annotations on Page {st.session_state.current_page + 1}:**")
            for idx, (i, ann) in enumerate(current_page_anns):
                with st.expander(f"{ann['type']} #{idx + 1}"):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        for key, value in ann.items():
                            if key != 'type' and key != 'page':
                                st.text(f"{key}: {value}")
                    with cols[1]:
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state.annotations.pop(i)
                            st.rerun()
        else:
            st.info("No annotations on this page yet.")
    else:
        st.info("No annotations added yet. Use the sidebar to add text, shapes, or other elements.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply and Download section
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 💾 Export PDF")
    
    if st.session_state.pdf_file and st.session_state.annotations:
        if st.button("🎨 Apply Annotations & Download", use_container_width=True, type="primary"):
            with st.spinner("Processing your PDF..."):
                try:
                    # Create overlay PDF with annotations
                    st.session_state.pdf_file.seek(0)
                    pdf_reader = PdfReader(st.session_state.pdf_file)
                    pdf_writer = PdfWriter()
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        
                        # Get page dimensions
                        page_width = float(page.mediabox.width)
                        page_height = float(page.mediabox.height)
                        
                        # Create overlay for this page
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                        
                        # Add annotations for this page
                        page_anns = [ann for ann in st.session_state.annotations if ann.get('page', 0) == page_num]
                        
                        for ann in page_anns:
                            if ann['type'] == "Add Text":
                                can.setFillColor(HexColor(ann['color']))
                                can.setFont("Helvetica", ann['font_size'])
                                can.drawString(ann['x'], ann['y'], ann['text'])
                                
                            elif ann['type'] in ["Add Rectangle", "Highlight"]:
                                can.setFillColor(HexColor(ann['fill_color']), alpha=ann['opacity'])
                                can.setStrokeColor(HexColor(ann['stroke_color']))
                                can.rect(ann['x'], ann['y'], ann['width'], ann['height'], 
                                        fill=1, stroke=1)
                                
                            elif ann['type'] == "Add Circle":
                                can.setFillColor(HexColor(ann['fill_color']), alpha=ann['opacity'])
                                can.setStrokeColor(HexColor(ann['stroke_color']))
                                can.circle(ann['x'], ann['y'], ann['radius'], fill=1, stroke=1)
                                
                            elif ann['type'] == "Add Line":
                                can.setStrokeColor(HexColor(ann['color']))
                                can.setLineWidth(ann['width'])
                                can.line(ann['x1'], ann['y1'], ann['x2'], ann['y2'])
                        
                        can.save()
                        
                        # Merge overlay with original page
                        packet.seek(0)
                        overlay_pdf = PdfReader(packet)
                        page.merge_page(overlay_pdf.pages[0])
                        pdf_writer.add_page(page)
                    
                    # Save to bytes
                    output = io.BytesIO()
                    pdf_writer.write(output)
                    output.seek(0)
                    
                    st.success("✅ PDF processed successfully!")
                    
                    st.download_button(
                        label="⬇️ Download Edited PDF",
                        data=output,
                        file_name="edited_document.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {str(e)}")
    elif not st.session_state.pdf_file:
        st.warning("⚠️ Please upload a PDF file first.")
    else:
        st.info("ℹ️ Add some annotations before exporting.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with features
st.markdown("---")
st.markdown("### ✨ Features")

feature_cols = st.columns(4)
with feature_cols[0]:
    st.markdown("**📝 Text Boxes**")
    st.caption("Add custom text anywhere")
with feature_cols[1]:
    st.markdown("**🔷 Shapes**")
    st.caption("Rectangles, circles, lines")
with feature_cols[2]:
    st.markdown("**🎨 Colors**")
    st.caption("Full color customization")
with feature_cols[3]:
    st.markdown("**💾 Export**")
    st.caption("Download edited PDFs")

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    1. **Upload** your PDF file using the upload section
    2. **Select** the page you want to edit (if multiple pages)
    3. **Choose** an editing tool from the sidebar (Text, Rectangle, Circle, Line, Highlight)
    4. **Customize** the tool settings (size, color, position, opacity)
    5. **Add** the annotation to your PDF by clicking "Add to PDF"
    6. **Repeat** steps 3-5 to add more annotations
    7. **Apply & Download** your edited PDF when finished
    
    **Tips:**
    - Use the position sliders to place elements precisely
    - The opacity slider is great for creating highlights
    - You can add multiple annotations before downloading
    - Clear all annotations to start over
    """)
