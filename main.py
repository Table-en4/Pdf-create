import tkinter as tk
from tkinter import filedialog, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class PDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gen PDF")
        self.root.geometry("800x600")

        self.text_widget = tk.Text(root, wrap="word", font=("Arial", 12))
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        self.save_button = tk.Button(root, text="Générer le PDF", command=self.generer_pdf)
        self.save_button.pack(pady=10)

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
                x = 50
                y = height - 50

                for ligne in texte.split("\n"):
                    if y < 50:
                        c.showPage()
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

