#include "knn_engine.hpp"
#include "httplib.h"
#include "json.hpp"
#include <iostream>
#include <string>

using json = nlohmann::json;

int main()
{
    std::cout << "[INFO] Инициализация сервера..." << std::endl;

    Matrix movie_matrix(1);
    if (!movie_matrix.load_from_file("../data/movie_embeddings.bin")) {
        std::cerr << "[ERROR] Ошибка загрузки матрицы векторов!" << std::endl;
        return 1;
    }
    std::cout << "[INFO] Матрица успешно загружена." << std::endl;

    KNN knn_engine(&movie_matrix, 20);
    if (!knn_engine.load_mapping("../data/movie_ids.bin")) {
        std::cerr << "[ERROR] Ошибка загрузки словаря ID!" << std::endl;
        return 1;
    }
    std::cout << "[INFO] Словарь ID успешно загружен." << std::endl;

    httplib::Server svr;

    svr.Get("/similar", [&knn_engine](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_param("movie_id")) {
            res.status = 400;
            res.set_content(json({{"error", "Missing movie_id parameter"}}).dump(), "application/json");
            return;
        }

        uint32_t movie_id = std::stoul(req.get_param_value("movie_id"));
        
        Neighbor* recs = knn_engine.get_similar_movies(movie_id);
        
        if (recs == nullptr) {
            res.status = 404;
            res.set_content(json({{"error", "Movie not found"}}).dump(), "application/json");
            return;
        }

        json response_json = json::array();
        for (int i = 0; i < 20; i++) {
            if (recs[i].sim > -0.5f) {
                response_json.push_back({
                    {"movie_id", recs[i].id},
                    {"similarity", recs[i].sim}
                });
            }
        }

        delete[] recs;

        res.set_content(response_json.dump(), "application/json");
    });

    svr.Post("/recommend", [&knn_engine](const httplib::Request& req, httplib::Response& res) {
        try {
            json req_json = json::parse(req.body);
            
            if (!req_json.contains("vector") || !req_json["vector"].is_array()) {
                res.status = 400;
                res.set_content(json({{"error", "Invalid JSON. Expected array 'vector'."}}).dump(), "application/json");
                return;
            }

            auto& json_array = req_json["vector"];
            int vector_size = json_array.size();
            
            float* user_vector = new float[vector_size];
            for (int i = 0; i < vector_size; ++i) {
                user_vector[i] = json_array[i].get<float>();
            }

            Neighbor* recs = knn_engine.get_recommendations_by_vector(user_vector);
            
            delete[] user_vector;

            if (recs == nullptr) {
                res.status = 500;
                res.set_content(json({{"error", "Internal server error"}}).dump(), "application/json");
                return;
            }

            json response_json = json::array();
            for (int i = 0; i < 20; i++) {
                response_json.push_back({
                    {"movie_id", recs[i].id},
                    {"similarity", recs[i].sim}
                });
            }

            delete[] recs;
            
            res.set_content(response_json.dump(), "application/json");

        } catch (const std::exception& e) {
            res.status = 400;
            res.set_content(json({{"error", std::string("JSON Parse Error: ") + e.what()}}).dump(), "application/json");
        }
    });

    std::cout << "Сервер запущен на http://localhost:8080" << std::endl;
    svr.listen("0.0.0.0", 8080);

    return 0;
}
