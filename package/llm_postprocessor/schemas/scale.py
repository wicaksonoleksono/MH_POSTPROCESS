class PHQScales:
    phq_scale = {
        0: "Tidak sama sekali — gejala tidak muncul dan tidak terbaca dalam percakapan.",
        1: "Beberapa kali — gejala muncul sesekali atau tersirat; dampaknya ringan dan mudah diabaikan.",
        2: "Cukup sering — gejala muncul berkali-kali dan mulai mengganggu aktivitas meski belum dominan.",
        3: "Dominan — gejala terus-menerus muncul secara jelas dan menghambat fungsi sehari-hari."
    }

    @classmethod
    def format_scale(cls, scale_name: str):
        """Format scale into 'Num: Description' lines."""
        scale = getattr(cls, scale_name, None)
        if not scale:
            raise ValueError(f"Scale '{scale_name}' not found.")
        return "\n".join([f"{num}: {desc}" for num, desc in scale.items()])
