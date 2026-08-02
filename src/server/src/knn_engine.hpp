#include "matrix.hpp"
#include <unordered_map>
#include <cstdint>

struct Neighbor {
    uint32_t id;
    float sim;
};

class KNN {
private:
    int k_neighbors;
    const Matrix* matrix;

    std::unordered_map<uint32_t, uint32_t> id_to_index;
    uint32_t* index_to_id = nullptr;

    void sift_down(Neighbor* heap, int size, int index) const;
    float dot_product(const float* vecA, const float* vecB, int dim) const;
    
    Neighbor* top_k(const Matrix& matrix, int user_id) const; 

public:
    KNN(const Matrix* mat, int neighbors = 20);

    bool load_mapping(const char* filename);

    Neighbor* get_similar_movies(uint32_t target_movie_id) const; 

    Neighbor* get_recommendations_by_vector(const float* user_profile_vector) const;
};