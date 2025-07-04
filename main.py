import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor

class PDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gen PDF")
        self.root.geometry("800x600")

        self.bg_color = "#FFFFFF"
        self.text_color = "#000000"

        self.text_widget = tk.Text(root, wrap="word", font=("Arial", 12))
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        #boutons
        self.color_bg_button = tk.Button(root, text="🎨 Choisir couleur de fond", command=self.choisir_couleur_fond)
        self.color_bg_button.pack(pady=5)

        self.color_text_button = tk.Button(root, text="✍️ Choisir couleur du texte", command=self.choisir_couleur_texte)
        self.color_text_button.pack(pady=5)

        self.save_button = tk.Button(root, text="📄 Générer le PDF", command=self.generer_pdf)
        self.save_button.pack(pady=10)

    def choisir_couleur_fond(self):
        couleur = colorchooser.askcolor(title="Choisir la couleur de fond")[1]
        if couleur:
            self.bg_color = couleur

    def choisir_couleur_texte(self):
        couleur = colorchooser.askcolor(title="Choisir la couleur du texte")[1]
        if couleur:
            self.text_color = couleur

    def generer_pdf(self):
        texte = self.text_widget.get("1.0", tk.END).strip()
        if not texte:
            messagebox.showwarning("Texte vide", "Le champ de texte est vide.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Enregistrer le PDF"
        )

        if file_path:
            try:
                c = canvas.Canvas(file_path, pagesize=A4)
                width, height = A4

                #set mon bg color
                c.setFillColor(HexColor(self.bg_color))
                c.rect(0, 0, width, height, fill=1)

                #set ma couleur texte
                c.setFillColor(HexColor(self.text_color))
                c.setFont("Helvetica", 12)

                x = 50
                y = height - 50

                for ligne in texte.split("\n"):
                    if y < 50:
                        c.showPage()
                        c.setFillColor(HexColor(self.bg_color))
                        c.rect(0, 0, width, height, fill=1)
                        c.setFillColor(HexColor(self.text_color))
                        c.setFont("Helvetica", 12)
                        y = height - 50
                    c.drawString(x, y, ligne)
                    y -= 14

                c.save()
                messagebox.showinfo("Succès", f"PDF enregistré avec succès :\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création du PDF :\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFApp(root)
    root.mainloop()
