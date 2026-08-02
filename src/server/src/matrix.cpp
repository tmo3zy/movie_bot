#include <iostream>
#include "matrix.hpp"

Matrix::Matrix(int n){
    M = n;
    N = n;
    values = new float*[n];

    for (int i = 0; i < n; i++)
    {
        values[i] = new float[n];
        for (int j = 0; j < n; j++) {
            values[i][j] = (i == j) ? 1.0f : 0.0f; // Исправлено для корректной единичной матрицы
        }
    }
}

Matrix::Matrix(int m, int n, float fill_value){
    M = m;
    N = n;
    values = new float*[m];

    for (int i = 0; i < m; i++)
    {
        values[i] = new float[n];
        for (int j = 0; j < n; j++) {
            values[i][j] = fill_value;
        }
    }
}

Matrix::Matrix(const Matrix& other) {
    M = other.M;
    N = other.N;
    
    values = new float*[M];
    
    for (int i = 0; i < M; i++) {
        values[i] = new float[N];
        for (int j = 0; j < N; j++) {
            values[i][j] = other.values[i][j];
        }
    }
}

Matrix::Matrix(Matrix&& other) : M(other.M), N(other.N), values(other.values){
    other.M = 0;
    other.N = 0;
    other.values = nullptr;
}

Matrix& Matrix::operator=(const Matrix& other){
    if (this == &other) return *this;
    
    for (int i = 0; i < M; i++){
        delete[] values[i];
    }
    delete[] values;

    M = other.M;
    N = other.N;
    
    values = new float*[M];
    
    for (int i = 0; i < M; i++) {
        values[i] = new float[N];
        for (int j = 0; j < N; j++) {
            values[i][j] = other.values[i][j];
        }
    }

    return *this;
}

Matrix& Matrix::operator=(Matrix&& other) {
    if (this == &other){
        return *this;
    }
    
    for (int i = 0; i < M; i++){
        delete[] values[i];
    }
    delete[] values;

    M = other.M;
    N = other.N;
    values = other.values;

    other.M = 0;
    other.N = 0;
    other.values = nullptr;

    return *this;
}

Matrix& Matrix::operator+=(const Matrix& other){
    this->add_in_place(other);
    return *this;
}

Matrix& Matrix::operator-=(const Matrix& other) {
    if (M != other.M || N != other.N){        
        throw "Ошибка! Размерности матриц при вычитании должны быть одинаковыми";
    }
    for (int i = 0; i < M; i++){
        for (int j = 0; j < N; j++){
            values[i][j] -= other.values[i][j];
        }
    }
    return *this;
}

Matrix& Matrix::operator*=(float inc){
    for (int i = 0; i < M; i++)
    {
        for (int j = 0; j < N; j++)
        {
            values[i][j] *= inc;
        }
    }
    return *this;
}

Matrix& Matrix::operator/=(float inc) {
    for (int i = 0; i < M; i++){
        for (int j = 0; j < N; j++){
            values[i][j] /= inc;
        }
    }
    return *this;
}

Matrix Matrix::operator+(const Matrix& other) const{
    Matrix result(*this);
    result.add_in_place(other);
    return result;
}

Matrix Matrix::operator-(const Matrix& other) const{
    if (M != other.M || N != other.N) {
        throw "Ошибка! Размерности матриц при сложении должны быть одинаковыми";
    }

    Matrix result(*this);

    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            result.values[i][j] -= other.values[i][j];
        }
    }
    return result;
}

Matrix Matrix::operator*(const Matrix& other) const{
    if (N != other.M) {
        throw "Ошибка! Количество стобцов первой матрицы должно совпадать с количеством строк второй матрицы";
    }

    Matrix dst(M, other.N, 0.0f);
    
    for (int i = 0; i < dst.M; i++)
    {
        for (int j = 0; j < dst.N; j++)
        {
            float sum = 0.0f;
            for (int k = 0; k < N; k++)
            {
                sum += values[i][k] * other.values[k][j];
            }
            dst.values[i][j] = sum;
        }
    }
    return dst;
}

Matrix Matrix::operator*(float inc) const{
    Matrix result(*this);
    result *= inc;
    return result;
}

Matrix Matrix::operator/(float inc) const{
    Matrix result(*this);
    
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            result.values[i][j] /= inc;
        }
    }
    return result;
}

Matrix operator*(float inc, const Matrix& m) {
    return m * inc;
}

Matrix operator-(const Matrix& m){
   return m * (-1.0f);
}

Matrix::~Matrix(){
    for (int i = 0; i < M; i++){
       delete[] values[i];
    }
    delete[] values;
}

float Matrix::get(int i, int j) const{
    return values[i][j];
}

const float* Matrix::get_row(int row_index) const {
    return values[row_index];
}

void Matrix::set(int i, int j, float value){
    values[i][j] = value;
}

int Matrix::get_width() const{
    return M;
}

int Matrix::get_height() const{
    return N;
}

void Matrix::negate(){
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            values[i][j] *= -1.0f;
        }
    }
}

void Matrix::add_in_place(const Matrix& other){
    if (M != other.M || N != other.N) {
        throw "Ошибка! Размерности матриц при сложении должны быть одинаковыми";
    }

    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            values[i][j] += other.values[i][j];
        }
    }
}

Matrix Matrix::multiply(const Matrix& other){
    return (*this) * other;
}

bool Matrix::load_from_file(const char* filename) {
    BaseFile file(filename, "rb");

    if (!file.is_open()) {
        std::cerr << "Не удалось открыть файл: " << filename << std::endl;
        return false;
    }

    if (values != nullptr) {
        for (int i = 0; i < M; i++) {
            delete[] values[i];
        }
        delete[] values;
        values = nullptr;
    }

    uint32_t dims[2];
    if (file.read_raw(dims, sizeof(dims)) != sizeof(dims)) {
         std::cerr << "Ошибка при чтении размерности матрицы!" << std::endl;
         return false;
    }
    
    M = dims[0];
    N = dims[1];

    values = new float*[M];
    size_t row_bytes = N * sizeof(float);

    for (int i = 0; i < M; i++) {
        values[i] = new float[N];
        
        if (file.read_raw(values[i], row_bytes) != row_bytes) {
            std::cerr << "Ошибка при чтении тела матрицы на строке " << i << std::endl;
            return false;
        }
    }

    return true;
}