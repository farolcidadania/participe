from django.utils.choices import BlankChoiceIterator
from django.template.defaultfilters import default
from django.db import models

class MateriaSettings(models.Model):
    camara_id = models.IntegerField(unique=True, null=True, blank=True)
    url = models.URLField()
    active = models.BooleanField(default=True)
    last_processed = models.DateTimeField(null=True, blank=True)
    save_html = models.BooleanField(default=False)
    
    desactivated = models.BooleanField(default=False)
    desactivated_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    desactivated_at = models.DateTimeField(null=True, blank=True)
    
    erro_messagem = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"tramitacao-{self.id}"

class MateriaHTML(models.Model):
    materia = models.ForeignKey(MateriaSettings, on_delete=models.CASCADE)
    identificador_cmf = models.CharField(max_length=50, unique=True)
    arquivo_html = models.FileField(upload_to='materias_brutas/%Y/%m/%d/%H/')

    processado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"materia-{self.id}"

class ProposicaoRaw(models.Model):
    api_id = models.CharField(max_length=100, unique=True) #capiture the timestamp.
    raw = models.JSONField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"raw-{self.api_id}"