import { app } from "../../scripts/app.js";
import { $el } from "../../scripts/ui.js";

app.registerExtension({
    name: "Comfy.SVGFullfill",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "SVGUploader") {
            nodeType.prototype.onNodeCreated = function () {
                console.log("Node created: SVGUploader");

                // 隐藏默认的字符串输入
                const svgInput = this.widgets.find(w => w.name === "svg_string");
                if (svgInput) {
                    svgInput.hidden = true;
                }

                // 创建上传按钮（先创建按钮，这样它会在预览区域上方）
                this.addWidget("button", "Upload SVG", null, () => {
                    console.log("Upload button clicked");
                    const fileInput = document.createElement("input");
                    fileInput.type = "file";
                    fileInput.accept = ".svg";
                    fileInput.style.display = "none";
                    document.body.appendChild(fileInput);

                    fileInput.onchange = async (e) => {
                        const file = e.target.files[0];
                        if (file) {
                            console.log("File selected:", file.name);
                            const reader = new FileReader();
                            reader.onload = async (e) => {
                                const svgContent = e.target.result;
                                console.log("SVG content loaded");

                                // 存储SVG内容
                                const svgInput = this.widgets.find(w => w.name === "svg_string");
                                if (svgInput) {
                                    svgInput.value = svgContent;
                                }

                                // 更新预览
                                try {
                                    console.log("Parsing SVG content...");
                                    const parser = new DOMParser();
                                    const doc = parser.parseFromString(svgContent, "image/svg+xml");
                                    const svgElement = doc.documentElement;

                                    if (!svgElement || svgElement.nodeName !== "svg") {
                                        throw new Error("Invalid SVG content");
                                    }

                                    console.log("Setting SVG attributes...");
                                    // 设置SVG属性
                                    svgElement.style.width = "100%";
                                    svgElement.style.height = "100%";
                                    svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");

                                    // 更新预览
                                    console.log("Updating preview container...");
                                    widget.div.innerHTML = "";
                                    widget.div.appendChild(svgElement.cloneNode(true));
                                    console.log("Preview updated successfully");

                                    // 强制重绘
                                    app.canvas.setDirty(true);

                                } catch (error) {
                                    console.error("Error updating preview:", error);
                                    widget.div.innerHTML = `
                                        <div style="color: red; text-align: center; padding: 10px;">
                                            Error loading SVG: ${error.message}
                                        </div>
                                    `;
                                }
                            };
                            reader.readAsText(file);
                        }
                        document.body.removeChild(fileInput);
                    };
                    fileInput.click();
                });

                // 创建预览widget
                const widget = {
                    type: "div",
                    name: "preview",
                    draw(ctx, node, widget_width, y, widget_height) {
                        const margin = 10;
                        const buttonHeight = 40; // 为按钮预留空间
                        const elRect = ctx.canvas.getBoundingClientRect();
                        const transform = new DOMMatrix()
                            .scaleSelf(
                                elRect.width / ctx.canvas.width,
                                elRect.height / ctx.canvas.height
                            )
                            .multiplySelf(ctx.getTransform())
                            .translateSelf(margin, margin + y + buttonHeight); // 添加buttonHeight偏移

                        Object.assign(this.div.style, {
                            transformOrigin: "0 0",
                            transform: transform,
                            position: "absolute",
                            left: document.querySelector('.comfy-menu').style.display === 'none' ? '60px' : '0',
                            top: "0",
                            width: `${widget_width - margin * 2}px`,
                            height: "200px", // 减小高度，给按钮留空间
                            zIndex: 1
                        });
                    }
                };

                // 创建预览容器
                widget.div = $el("div", {
                    style: {
                        width: "100%",
                        height: "100%",
                        border: "2px solid #ccc",
                        borderRadius: "4px",
                        backgroundColor: "#f0f0f0",
                        overflow: "hidden",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                    }
                });

                // 创建占位符
                const placeholderText = $el("div", {
                    textContent: "SVG Preview",
                    style: {
                        color: "#666",
                        textAlign: "center",
                        userSelect: "none",
                        pointerEvents: "none"
                    }
                });
                widget.div.appendChild(placeholderText);

                // 添加预览widget到节点
                document.body.appendChild(widget.div);
                this.addCustomWidget(widget);

                // 设置节点大小
                this.setSize([220, 320]);

                // 清理函数
                const onRemoved = this.onRemoved;
                this.onRemoved = () => {
                    widget.div.remove();
                    return onRemoved?.();
                };
            };
        }
    }
});

