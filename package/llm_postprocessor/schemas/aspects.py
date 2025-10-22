class PHQAspects:
    
    DEFAULT_ASPECTS = [
        {
            "name": "Anhedonia atau Kehilangan Minat atau Kesenangan",
            "description": "Pengguna kehilangan minat atau kesenangan dalam hampir semua aktivitas sehari-hari. Jika kegiatan yang dulu bikin semangat sekarang terasa hambar, menurutmu apa yang bikin rasanya berubah?"
        },
        {
            "name": "Mood Depresi",
            "description": "Pengguna mengalami suasana hati yang tertekan hampir sepanjang hari, hampir setiap hari. Kalau belakangan ini terasa sedih terus, menurutmu apa yang biasanya memicu atau memperberat perasaan itu?"
        },
        {
            "name": "Perubahan Berat Badan atau Nafsu Makan",
            "description": "Pengguna mengalami penurunan atau peningkatan berat badan yang signifikan, atau perubahan nafsu makan. Kalau pola makanmu berubah, apa yang biasanya mempengaruhi—stres, ritme harian, atau hal lain?"
        },
        {
            "name": "Gangguan Tidur",
            "description": "Pengguna mengalami insomnia atau hipersomnia hampir setiap hari. Saat tidur berantakan, apa yang biasanya membuatmu susah/lelap—pikiran tertentu, jadwal, atau kebiasaan sebelum tidur?"
        },
        {
            "name": "Retardasi atau Agitasi Psikomotor",
            "description": "Pengguna menunjukkan perlambatan gerakan/pembicaraan atau agitasi yang dapat diamati oleh orang lain. Tanyakan pada teman apakah mereka melihat kamu lebih lambat atau lebih gelisah dari biasanya; menurutmu apa yang memicu perubahan ritme itu?"
        },
        {
            "name": "Kelelahan atau Kehilangan Energi",
            "description": "Pengguna merasa lelah atau kehilangan energi hampir setiap hari. Saat energi cepat turun, biasanya apa yang terjadi sebelumnya—kurang tidur, beban pikiran, atau pola kerja?"
        },
        {
            "name": "Perasaan Tidak Berharga atau Bersalah Berlebihan",
            "description": "Pengguna merasakan perasaan tidak berharga atau rasa bersalah yang berlebihan atau tidak tepat. Kalau rasa bersalah atau merasa tidak cukup muncul, biasanya dipicu oleh situasi atau pikiran seperti apa?"
        },
        {
            "name": "Gangguan Konsentrasi atau Pengambilan Keputusan",
            "description": "Pengguna mengalami kesulitan dalam konsentrasi dan fungsi eksekutif, termasuk membuat keputusan, hampir setiap hari. Jika fokus gampang buyar, apa yang biasanya mengganggu—notifikasi, kekhawatiran tertentu, atau kelelahan?"
        },
        {
            "name": "Pikiran tentang Kematian atau Bunuh Diri",
            "description": "Pengguna memiliki pikiran berulang tentang kematian, ide bunuh diri, atau percobaan bunuh diri. Jika pikiran seperti itu muncul, kapan biasanya muncul dan apa yang membuatnya terasa lebih kuat?"
        }
    ]

    @classmethod
    def as_object(cls):
        """Return dict with underscored names as keys and descriptions as values."""
        return {
            aspect["name"].replace(" ", "_"): aspect["description"]
            for aspect in cls.DEFAULT_ASPECTS
        }

    @classmethod
    def get_aspect(cls):
        """Return string formatted as 'name: description' lines."""
        aspects = cls.as_object()
        return "\n".join([f"{name}: {desc}" for name, desc in aspects.items()])

