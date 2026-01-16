from ebooklib import epub


def add_css_style(book: epub.EpubBook) -> None:
    """添加精美的多看风格CSS样式到EPUB书籍。"""
    style = """
    /* =====================================
       精美EPUB样式 - 基于多看模板优化设计
       ===================================== */
    
    /* 基础重置与字体设置 */
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        /* 多级字体回退，确保最佳显示效果 */
        font-family: "DK-SONGTI", "方正宋三简体", "方正书宋", "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", "宋体", serif;
        font-size: 16px;
        line-height: 1.8;
        color: #2c2c2c;
        background: #fefefe;
        max-width: 100%;
        margin: 0 auto;
        padding: 2rem 1.5rem;
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* =====================================
       卷/部/篇标题样式 (最高级别)
       ===================================== */
    .volume-title {
        font-family: "DK-XIAOBIAOSONG", "方正小标宋简体", "STZhongsong", "华文中宋", serif;
        font-size: 2.4em;
        font-weight: normal;
        text-align: center;
        color: #91531d;
        margin: 3rem 0 4rem 0;
        padding: 2rem 0;
        border-bottom: 4px solid #e8c696;
        text-shadow: 1px 1px 3px rgba(145, 83, 29, 0.2);
        position: relative;
    }
    
    .volume-title::before {
        content: "";
        position: absolute;
        top: -0.5rem;
        left: 50%;
        transform: translateX(-50%);
        width: 60%;
        height: 2px;
        background: linear-gradient(to right, transparent, #91531d, transparent);
    }
    
    /* =====================================
       章标题样式 (中级别)
       ===================================== */
    .chapter-title {
        font-family: "DK-XIAOBIAOSONG", "方正小标宋简体", "STZhongsong", "华文中宋", serif;
        font-size: 2em;
        font-weight: normal;
        text-align: center;
        color: #1f4a92;
        margin: 2.5rem 0 3rem 0;
        padding: 1.5rem 0;
        border-bottom: 2px solid #1f4a92;
        position: relative;
    }
    
    .chapter-title::after {
        content: "◊";
        position: absolute;
        bottom: -0.8rem;
        left: 50%;
        transform: translateX(-50%);
        color: #1f4a92;
        font-size: 0.8em;
        background: #fefefe;
        padding: 0 0.5rem;
    }
    
    /* =====================================
       节标题样式 (低级别)
       ===================================== */
    .section-title {
        font-family: "DK-HEITI", "方正兰亭黑简体", "SimHei", "黑体", sans-serif;
        font-size: 1.4em;
        font-weight: normal;
        color: #478686;
        margin: 2rem 0 1.5rem 0;
        padding: 0.8rem 0 0.8rem 1.2rem;
        border-left: 5px solid #478686;
        background: linear-gradient(to right, rgba(71, 134, 134, 0.05), transparent);
        position: relative;
    }
    
    .section-title::before {
        content: "▸";
        position: absolute;
        left: -0.2rem;
        color: #478686;
        font-size: 0.8em;
    }
    
    /* =====================================
       兼容性标题样式
       ===================================== */
    h1 {
        font-family: "DK-XIAOBIAOSONG", "方正小标宋简体", "STZhongsong", "华文中宋", serif;
        font-size: 2em;
        font-weight: normal;
        text-align: center;
        color: #1f4a92;
        margin: 2.5rem 0 3rem 0;
        padding: 1.5rem 0;
        border-bottom: 2px solid #1f4a92;
    }
    
    h2 {
        font-family: "DK-HEITI", "方正兰亭黑简体", "SimHei", "黑体", sans-serif;
        font-size: 1.4em;
        font-weight: normal;
        color: #478686;
        margin: 2rem 0 1.5rem 0;
        padding: 0.8rem 0 0.8rem 1.2rem;
        border-left: 5px solid #478686;
    }
    
    h3 {
        font-family: "DK-HEITI", "方正兰亭黑简体", "SimHei", "黑体", sans-serif;
        font-size: 1.2em;
        font-weight: normal;
        color: #91531d;
        margin: 1.8rem 0 1.2rem 2rem;
    }
    
    /* =====================================
       正文段落样式
       ===================================== */
    p {
        font-family: "DK-SONGTI", "方正宋三简体", "方正书宋", "Noto Serif CJK SC", "SimSun", "宋体", serif;
        font-size: 16px;
        line-height: 1.8;
        text-indent: 2em;
        margin-bottom: 1.2em;
        text-align: justify;
        word-wrap: break-word;
        color: #2c2c2c;
    }
    
    /* 特殊段落样式 */
    p.text0 {
        text-indent: 0em;
    }
    
    p.reference {
        font-family: "DK-KAITI", "方正楷体", "华文楷体", "KaiTi", "楷体", serif;
        font-style: italic;
        color: #555;
        background: rgba(145, 83, 29, 0.03);
        padding: 0.8rem 1.2rem;
        margin: 1.5rem 0;
        border-left: 3px solid #91531d;
        text-indent: 2em;
    }
    
    p.reference-center {
        font-family: "DK-KAITI", "方正楷体", "华文楷体", "KaiTi", "楷体", serif;
        text-align: center;
        font-style: italic;
        color: #666;
        margin: 1.5rem 0;
        text-indent: 0em;
    }
    
    /* =====================================
       预格式化文本样式
       ===================================== */
    pre {
        font-family: "DK-SONGTI", "方正宋三简体", "方正书宋", "Noto Serif CJK SC", "SimSun", "宋体", serif;
        font-size: 16px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 1.5rem 0;
        padding: 0;
        background: transparent;
        border: none;
        color: #2c2c2c;
    }
    
    /* =====================================
       图片和图注样式
       ===================================== */
    img.duokan-image {
        width: 100%;
        height: auto;
        margin: 1.5rem 0;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .duokan-image-single {
        width: 100%;
        text-align: center;
        margin: 1.5rem 0;
    }
    
    p.duokan-note {
        font-family: "DK-KAITI", "方正楷体", "华文楷体", "KaiTi", "楷体", serif;
        font-size: 14px;
        color: #666;
        text-align: center;
        text-indent: 0em;
        margin: 0.5rem 0 1.5rem 0;
        font-style: italic;
    }
    
    /* =====================================
       强调和装饰样式
       ===================================== */
    .emphasis {
        color: #91531d;
        font-weight: bold;
    }
    
    .kaiti {
        font-family: "DK-KAITI", "方正楷体", "华文楷体", "KaiTi", "楷体", serif;
    }
    
    .heiti {
        font-family: "DK-HEITI", "方正兰亭黑简体", "SimHei", "黑体", sans-serif;
    }
    
    .songti {
        font-family: "DK-SONGTI", "方正宋三简体", "方正书宋", "SimSun", "宋体", serif;
    }
    
    /* =====================================
       分隔线和装饰元素
       ===================================== */
    .separator {
        text-align: center;
        margin: 3rem 0;
        color: #91531d;
        font-size: 1.2em;
    }
    
    .separator::before {
        content: "❋ ❋ ❋";
        color: #91531d;
        opacity: 0.6;
    }
    
    /* =====================================
       响应式设计
       ===================================== */
    @media screen and (max-width: 768px) {
        body {
            padding: 1rem;
            font-size: 15px;
        }
        
        .volume-title {
            font-size: 2em;
            margin: 2rem 0 3rem 0;
            padding: 1.5rem 0;
        }
        
        .chapter-title {
            font-size: 1.7em;
            margin: 2rem 0 2.5rem 0;
            padding: 1.2rem 0;
        }
        
        .section-title {
            font-size: 1.2em;
            margin: 1.5rem 0 1.2rem 0;
            padding: 0.6rem 0 0.6rem 1rem;
        }
        
        h1 {
            font-size: 1.7em;
            margin: 2rem 0 2.5rem 0;
        }
        
        h2 {
            font-size: 1.2em;
            margin: 1.5rem 0 1.2rem 0;
        }
        
        p {
            font-size: 15px;
            line-height: 1.7;
        }
        
        pre {
            font-size: 15px;
            line-height: 1.7;
        }
    }
    
    @media screen and (max-width: 480px) {
        body {
            padding: 0.8rem;
            font-size: 14px;
        }
        
        .volume-title {
            font-size: 1.8em;
        }
        
        .chapter-title {
            font-size: 1.5em;
        }
        
        .section-title {
            font-size: 1.1em;
        }
        
        p, pre {
            font-size: 14px;
            line-height: 1.6;
        }
    }
    
    /* =====================================
       打印样式优化
       ===================================== */
    @media print {
        body {
            background: white;
            color: black;
            padding: 0;
        }
        
        .volume-title, .chapter-title, .section-title {
            page-break-after: avoid;
        }
        
        p {
            orphans: 3;
            widows: 3;
        }
        
        img {
            max-width: 100%;
            page-break-inside: avoid;
        }
    }
    
    /* =====================================
       中文排版优化
       ===================================== */
    .chinese-text {
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-variant-east-asian: proportional-width;
        font-feature-settings: "kern" 1;
    }
    
    /* 禁用连字和优化间距 */
    body {
        font-variant-ligatures: none;
        font-kerning: auto;
        text-size-adjust: 100%;
        -webkit-text-size-adjust: 100%;
    }
    """
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style.encode('utf-8')
    )
    book.add_item(nav_css)