def average_rating(ratings):
    """Counts average rating from list of ratings"""
    if len(ratings) == 0:
        return None
    ratings_sum = 0
    for rating in ratings:
        ratings_sum += rating
    return ratings_sum / len(ratings)
