class PHQScales:
    phq_scale = {
        0: "Tidak sama sekali",
        1: "Beberapa hari",
        2: "Lebih dari setengah hari",
        3: "Hampir setiap hari"
    }

    operational_scale = {
        0: "Tidak ada: tidak ditemukan indikasi gejala.",
        1: "Sesekali / tersirat: muncul beberapa hari; gejala tersirat atau disebut sambil lalu.",
        2: "Cukup sering / jelas: terjadi beberapa kali; gejala disebutkan cukup jelas, namun belum mendominasi.",
        3: "Sering / dominan: muncul berulang; disebutkan secara eksplisit sebagai keluhan utama."
    }

    @classmethod
    def format_scale(cls, scale_name: str):
        """Format scale into 'Num: Description' lines."""
        scale = getattr(cls, scale_name, None)
        if not scale:
            raise ValueError(f"Scale '{scale_name}' not found.")
        return "\n".join([f"{num}: {desc}" for num, desc in scale.items()])
