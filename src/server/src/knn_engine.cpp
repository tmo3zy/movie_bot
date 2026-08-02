#include "knn_engine.hpp"
#include "basefile.hpp"
#include <iostream>

KNN::KNN(const Matrix* mat, int neighbors) : matrix(mat), k_neighbors(neighbors) {
    index_to_id = nullptr;
}

KNN::~KNN() {
    if (index_to_id != nullptr) {
        delete[] index_to_id;
    }
}

bool KNN::load_mapping(const char* filename) {
    BaseFile file(filename, "rb");
    if (!file.is_open()) {
        std::cerr << "Не удалось открыть файл маппинга: " << filename << std::endl;
        return false;
    }

    uint32_t M = matrix->get_width(); 
    if (M == 0) {
        std::cerr << "Сначала загрузите матрицу векторов!" << std::endl;
        return false;
    }

    if (index_to_id != nullptr) {
        delete[] index_to_id;
    }
    index_to_id = new uint32_t[M];

    size_t bytes_to_read = M * sizeof(uint32_t);
    if (file.read_raw(index_to_id, bytes_to_read) != bytes_to_read) {
        std::cerr << "Ошибка чтения файла ID!" << std::endl;
        return false;
    }

    id_to_index.reserve(M);
    id_to_index.clear();

    for (uint32_t i = 0; i < M; i++) {
        uint32_t tmdb_id = index_to_id[i];
        id_to_index[tmdb_id] = i; 
    }

    return true;
}

float KNN::dot_product(const float* vecA, const float* vecB, int dim) const {
    float result = 0.0f;
    
    for (int i = 0; i < dim; i++)
    {
        result += vecA[i] * vecB[i];
    }
    
    return result;
}

void KNN::sift_down(Neighbor* heap, int size, int index) const {
    while (true) {
        int left = 2 * index + 1;
        int right = 2 * index + 2;
        int smallest = index;

        if (left < size && heap[left].sim < heap[smallest].sim) {
            smallest = left;
        }

        if (right < size && heap[right].sim < heap[smallest].sim) {
            smallest = right;
        }

        if (smallest == index) {
            break;
        }

        Neighbor tmp = heap[index];
        heap[index] = heap[smallest];
        heap[smallest] = tmp;
        
        index = smallest;
    }
}

Neighbor* KNN::get_recommendations_by_vector(const float* user_profile_vector) const {
    if (matrix == nullptr || matrix->get_width() == 0) return nullptr;

    Neighbor* heap = new Neighbor[k_neighbors];
    
    for (int i = 0; i < k_neighbors; ++i) {
        heap[i].id = index_to_id[i];
        heap[i].sim = dot_product(user_profile_vector, matrix->get_row(i), matrix->get_height());
    }

    for (int i = k_neighbors / 2 - 1; i >= 0; --i) {
        sift_down(heap, k_neighbors, i);
    }

    for (uint32_t i = k_neighbors; i < matrix->get_width(); ++i) {
        float sim = dot_product(user_profile_vector, matrix->get_row(i), matrix->get_height());

        if (sim > heap[0].sim)
        {
            heap[0].id = index_to_id[i];
            heap[0].sim = sim;
            sift_down(heap, k_neighbors, 0);
        }
        
    }

    return heap;
}


Neighbor* KNN::get_similar_movies(uint32_t target_movie_id) const {
    auto it = id_to_index.find(target_movie_id);
    if (it == id_to_index.end()) {
        std::cerr << "Фильм с ID " << target_movie_id << " не найден в словаре!" << std::endl;
        return nullptr;
    }

    uint32_t target_index = it->second;
    const float* target_vector = matrix->get_row(target_index);

    Neighbor* raw_recommendations = get_recommendations_by_vector(target_vector);
    if (raw_recommendations == nullptr) return nullptr;

    int duplicate_index = -1;
    for (int i = 0; i < k_neighbors; ++i) {
        if (raw_recommendations[i].id == target_movie_id) {
            duplicate_index = i;
            break;
        }
    }

    if (duplicate_index != -1) {
        raw_recommendations[duplicate_index].sim = -1.0f;
    }

    return raw_recommendations;
}