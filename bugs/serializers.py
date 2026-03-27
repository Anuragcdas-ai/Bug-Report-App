from rest_framework import serializers

class DeveloperBugStatsSerializer(serializers.Serializer):
    username = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()

    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    pending = serializers.IntegerField()