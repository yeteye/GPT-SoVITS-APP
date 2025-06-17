import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

// 定义通用响应接口
export interface MyResponse {
    data: any;
    msg: string;
    code: number;
}

// 创建 axios 实例
const instance = axios.create({
    // 可以在此设置通用配置，例如 baseURL 或超时时间
    baseURL: 'http://localhost:8080', // 替换为后端接口的基础地址
    timeout: 5000, // 请求超时时间
});

// 通用请求方法
export function request<T>(config: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return instance.request<T>(config);
}
